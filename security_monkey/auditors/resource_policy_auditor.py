#     Copyright 2014 Netflix, Inc.
#
#     Licensed under the Apache License, Version 2.0 (the "License");
#     you may not use this file except in compliance with the License.
#     You may obtain a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an "AS IS" BASIS,
#     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#     See the License for the specific language governing permissions and
#     limitations under the License.
"""
.. module: security_monkey.auditors.resource_policy_auditor
    :platform: Unix

.. version:: $$VERSION$$
.. moduleauthor:: Patrick Kelley <patrick@netflix.com>

"""
from security_monkey import app
from security_monkey.auditor import Auditor, Entity
from security_monkey.datastore import Account

from policyuniverse.arn import ARN
from policyuniverse.policy import Policy
from policyuniverse.statement import Statement

import json
import dpath.util
from dpath.exceptions import PathNotFound
import ipaddr



class ResourcePolicyAuditor(Auditor):

    def __init__(self, accounts=None, debug=False):
        super(ResourcePolicyAuditor, self).__init__(accounts=accounts, debug=debug)
        self.policy_keys = ['Policy']

    def load_policies(self, item):
        """For a given item, return a list of all resource policies.
        
        Most items only have a single resource policy, typically found 
        inside the config with the key, "Policy".
        
        Some technologies have multiple resource policies.  A lambda function
        is an example of an item with multiple resource policies.
        
        The lambda function auditor can define a list of `policy_keys`.  Each
        item in this list is the dpath to one of the resource policies.
        
        The `policy_keys` defaults to ['Policy'] unless overriden by a subclass.
        
        Returns:
            list of Policy objects
        """
        policies = list()
        for key in self.policy_keys:
            try:
                policy = dpath.util.values(item.config, key, separator='$')
                if isinstance(policy, list):
                    for p in policy:
                        if not p:
                            continue
                        if isinstance(p, list):
                            policies.extend([Policy(pp) for pp in p])
                        else:
                            policies.append(Policy(p))
                else:
                    policies.append(Policy(policy))
            except PathNotFound:
                continue
        return policies

    def check_internet_accessible(self, item):
        policies = self.load_policies(item)
        for policy in policies:
            if policy.is_internet_accessible():
                entity = Entity(category='principal', value='*')
                actions = list(policy.internet_accessible_actions())
                self.record_internet_access(item, entity, actions)

    def check_friendly_cross_account(self, item):
        policies = self.load_policies(item)
        for policy in policies:
            for statement in policy.statements:
                if statement.effect != 'Allow':
                    continue
                for who in statement.whos_allowed():
                    entity = Entity.from_tuple(who)
                    if 'FRIENDLY' in self.inspect_entity(entity, item):
                        self.record_friendly_access(item, entity, list(statement.actions))

    def check_thirdparty_cross_account(self, item):
        policies = self.load_policies(item)
        for policy in policies:
            for statement in policy.statements:
                if statement.effect != 'Allow':
                    continue
                for who in statement.whos_allowed():
                    entity = Entity.from_tuple(who)
                    if 'THIRDPARTY' in self.inspect_entity(entity, item):
                        self.record_thirdparty_access(item, entity, list(statement.actions))

    def check_unknown_cross_account(self, item):
        policies = self.load_policies(item)
        for policy in policies:
            if policy.is_internet_accessible():
                continue
            for statement in policy.statements:
                if statement.effect != 'Allow':
                    continue
                for who in statement.whos_allowed():
                    if who.value == '*' and who.category == 'principal':
                        continue

                    # Ignore Service Principals
                    if who.category == 'principal':
                        arn = ARN(who.value)
                        if arn.service:
                            continue

                    entity = Entity.from_tuple(who)
                    if 'UNKNOWN' in self.inspect_entity(entity, item):
                        self.record_unknown_access(item, entity, list(statement.actions))

    def check_root_cross_account(self, item):
        policies = self.load_policies(item)
        for policy in policies:
            for statement in policy.statements:
                if statement.effect != 'Allow':
                    continue
                for who in statement.whos_allowed():
                    if who.category not in ['arn', 'principal']:
                        continue
                    if who.value == '*':
                        continue
                    arn = ARN(who.value)
                    entity = Entity.from_tuple(who)
                    if arn.root and self.inspect_entity(entity, item).intersection(set(['FRIENDLY', 'THIRDPARTY', 'UNKNOWN'])):
                        self.record_cross_account_root(item, entity, list(statement.actions))

    def inspect_entity(self, entity, item):
        """A entity can represent an:
        
        - ARN
        - Account Number
        - UserID
        - CIDR
        - VPC
        - VPCE
        
        Determine if the who is in our current account. Add the associated account
        to the entity.
        
        Return:
            'SAME' - The who is in our same account.
            'FRIENDLY' - The who is in an account Security Monkey knows about.
            'UNKNOWN' - The who is in an account Security Monkey does not know about.
        """
        same = Account.query.filter(Account.name == item.account).first()
        
        if entity.category in ['arn', 'principal']:
            return self.inspect_entity_arn(entity, same, item)
        if entity.category == 'account':
            return set([self.inspect_entity_account(entity, entity.value, same)])
        if entity.category == 'userid':
            return self.inspect_entity_userid(entity, same)
        if entity.category == 'cidr':
            return self.inspect_entity_cidr(entity, same)
        if entity.category == 'vpc':
            return self.inspect_entity_vpc(entity, same)
        if entity.category == 'vpce':
            return self.inspect_entity_vpce(entity, same)
        
        return 'ERROR'
    
    def inspect_entity_arn(self, entity, same, item):
        arn_input = entity.value
        if arn_input == '*':
            return set(['UNKNOWN'])

        arn = ARN(arn_input)
        if arn.error:
            self.record_arn_parse_issue(item, arn_input)

        if arn.tech == 's3':
            return self.inspect_entity_s3(entity, arn.name, same)

        return set([self.inspect_entity_account(entity, arn.account_number, same)])

    def inspect_entity_account(self, entity, account_number, same):

        # Enrich the entity with account data if available.
        for account in self.OBJECT_STORE['ACCOUNTS']['DESCRIPTIONS']:
            if account['identifier'] == account_number:
                entity.account_name = account['name']
                entity.account_identifier = account['identifier']
                break

        if account_number == '000000000000':
            return 'SAME'
        if account_number == same.identifier:
            return 'SAME'
        if account_number in self.OBJECT_STORE['ACCOUNTS']['FRIENDLY']:
            return 'FRIENDLY'
        if account_number in self.OBJECT_STORE['ACCOUNTS']['THIRDPARTY']:
            return 'THIRDPARTY'
        return 'UNKNOWN'

    def inspect_entity_s3(self, entity, bucket_name, same):
        return self.inspect_entity_generic('s3', entity, bucket_name, same)

    def inspect_entity_userid(self, entity, same):
        return self.inspect_entity_generic('userid', entity, entity.value.split(':')[0], same)

    def inspect_entity_vpc(self, entity, same):
        return self.inspect_entity_generic('vpc', entity, entity.value, same)

    def inspect_entity_vpce(self, entity, same):
        return self.inspect_entity_generic('vpce', entity, entity.value, same)

    def inspect_entity_cidr(self, entity, same):
        values = set()
        for str_cidr in self.OBJECT_STORE.get('cidr', []):
            if ipaddr.IPNetwork(entity.value) in ipaddr.IPNetwork(str_cidr):
                for account in self.OBJECT_STORE['cidr'].get(str_cidr, []):
                    values.add(self.inspect_entity_account(entity, account, same))
        if not values:
            return set(['UNKNOWN'])
        return values

    def inspect_entity_generic(self, key, entity, item, same):
        if item in self.OBJECT_STORE.get(key, []):
            values = set()
            for account in self.OBJECT_STORE[key].get(item, []):
                values.add(self.inspect_entity_account(entity, account, same))
            return values
        return set(['UNKNOWN'])
