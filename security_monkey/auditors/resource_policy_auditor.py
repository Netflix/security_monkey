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
from security_monkey.auditor import Auditor, Categories, Entity
from security_monkey.datastore import Account, Item, Technology, NetworkWhitelistEntry

from policyuniverse.arn import ARN
from policyuniverse.policy import Policy
from policyuniverse.statement import Statement
from threading import Lock
import json
import dpath.util
from dpath.exceptions import PathNotFound
from collections import defaultdict
import ipaddr
import netaddr


def add(to, key, value):
    if not key:
        return
    if key in to:
        to[key].add(value)
    else:
        to[key] = set([value])

class ResourcePolicyAuditor(Auditor):
    OBJECT_STORE = defaultdict(dict)
    OBJECT_STORE_LOCK = Lock()

    def __init__(self, accounts=None, debug=False):
        super(ResourcePolicyAuditor, self).__init__(accounts=accounts, debug=debug)
        self.policy_keys = ['Policy']

    def prep_for_audit(self):
        self._load_object_store()

    @classmethod
    def _load_object_store(cls):
        with cls.OBJECT_STORE_LOCK:
            if not cls.OBJECT_STORE:
                cls._load_s3_buckets()
                cls._load_userids()
                cls._load_accounts()
                cls._load_elasticips()
                cls._load_vpcs()
                cls._load_vpces()
                cls._load_natgateways()
                cls._load_network_whitelist()
                cls._merge_cidrs()

    @classmethod
    def _merge_cidrs(cls):
        """
        We learned about CIDRs from the following functions:
        -   _load_elasticips()
        -   _load_vpcs()
        -   _load_vpces()
        -   _load_natgateways()
        -   _load_network_whitelist()

        These cidr's are stored in the OBJECT_STORE in a way that is not optimal:

            OBJECT_STORE['cidr']['54.0.0.1'] = set(['123456789012'])
            OBJECT_STORE['cidr']['54.0.0.0'] = set(['123456789012'])
            ...
            OBJECT_STORE['cidr']['54.0.0.255/32'] = set(['123456789012'])

        The above example is attempting to illustrate that account `123456789012`
        contains `54.0.0.0/24`, maybe from 256 elastic IPs.

        If a resource policy were attempting to ingress this range as a `/24` instead
        of as individual IPs, it would not work.  We need to use the `cidr_merge`
        method from the `netaddr` library.  We need to preserve the account identifiers
        that are associated with each cidr as well.

        # Using:
        # https://netaddr.readthedocs.io/en/latest/tutorial_01.html?highlight=summarize#summarizing-list-of-addresses-and-subnets
        # import netaddr
        # netaddr.cidr_merge(ip_list)

        Step 1: Group CIDRs by account:
        #   ['123456789012'] = ['IP', 'IP']

        Step 2:
        Merge each account's cidr's separately and repalce the OBJECT_STORE['cidr'] entry.

        Return:
            `None`.  Mutates the cls.OBJECT_STORE['cidr'] datastructure.
        """
        if not 'cidr' in cls.OBJECT_STORE:
            return

        # step 1
        merged = defaultdict(set)
        for cidr, accounts in cls.OBJECT_STORE['cidr'].items():
            for account in accounts:
                merged[account].add(cidr)

        del cls.OBJECT_STORE['cidr']

        # step 2
        for account, cidrs in merged.items():
            merged_cidrs = netaddr.cidr_merge(cidrs)
            for cidr in merged_cidrs:
                add(cls.OBJECT_STORE['cidr'], cidr, account)

    @classmethod
    def _load_s3_buckets(cls):
        """Store the S3 bucket ARNs from all our accounts"""
        results = cls._load_related_items('s3')
        for item in results:
            add(cls.OBJECT_STORE['s3'], item.name, item.account.identifier)

    @classmethod
    def _load_vpcs(cls):
        """Store the VPC IDs. Also, extract & store network/NAT ranges."""
        results = cls._load_related_items('vpc')
        for item in results:
            add(cls.OBJECT_STORE['vpc'], item.latest_config.get('id'), item.account.identifier)
            add(cls.OBJECT_STORE['cidr'], item.latest_config.get('cidr_block'), item.account.identifier)

            vpcnat_tags = unicode(item.latest_config.get('tags', {}).get('vpcnat', ''))
            vpcnat_tag_cidrs = vpcnat_tags.split(',')
            for vpcnat_tag_cidr in vpcnat_tag_cidrs:
                add(cls.OBJECT_STORE['cidr'], vpcnat_tag_cidr.strip(), item.account.identifier)

    @classmethod
    def _load_vpces(cls):
        """Store the VPC Endpoint IDs."""
        results = cls._load_related_items('endpoint')
        for item in results:
            add(cls.OBJECT_STORE['vpce'], item.latest_config.get('id'), item.account.identifier)

    @classmethod
    def _load_elasticips(cls):
        """Store the Elastic IPs."""
        results = cls._load_related_items('elasticip')
        for item in results:
            add(cls.OBJECT_STORE['cidr'], item.latest_config.get('public_ip'), item.account.identifier)
            add(cls.OBJECT_STORE['cidr'], item.latest_config.get('private_ip_address'), item.account.identifier)

    @classmethod
    def _load_natgateways(cls):
        """Store the NAT Gateway CIDRs."""
        results = cls._load_related_items('natgateway')
        for gateway in results:
            for address in gateway.latest_config.get('nat_gateway_addresses', []):
                add(cls.OBJECT_STORE['cidr'], address['public_ip'], gateway.account.identifier)
                add(cls.OBJECT_STORE['cidr'], address['private_ip'], gateway.account.identifier)

    @classmethod
    def _load_network_whitelist(cls):
        """Stores the Network Whitelist CIDRs."""
        whitelist_entries = NetworkWhitelistEntry.query.all()
        for entry in whitelist_entries:
            add(cls.OBJECT_STORE['cidr'], entry.cidr, '000000000000')

    @classmethod
    def _load_userids(cls):
        """Store the UserIDs from all IAMUsers and IAMRoles."""
        user_results = cls._load_related_items('iamuser')
        role_results = cls._load_related_items('iamrole')

        for item in user_results:
            add(cls.OBJECT_STORE['userid'], item.latest_config.get('UserId'), item.account.identifier)

        for item in role_results:
            add(cls.OBJECT_STORE['userid'], item.latest_config.get('RoleId'), item.account.identifier)

    @classmethod
    def _load_accounts(cls):
        """Store the account IDs of all friendly/thirdparty accounts."""
        friendly_accounts = Account.query.filter(Account.third_party == False).all()
        third_party = Account.query.filter(Account.third_party == True).all()

        cls.OBJECT_STORE['ACCOUNTS']['DESCRIPTIONS'] = list()
        cls.OBJECT_STORE['ACCOUNTS']['FRIENDLY'] = set()
        cls.OBJECT_STORE['ACCOUNTS']['THIRDPARTY'] = set()

        for account in friendly_accounts:
            add(cls.OBJECT_STORE['ACCOUNTS'], 'FRIENDLY', account.identifier)
            cls.OBJECT_STORE['ACCOUNTS']['DESCRIPTIONS'].append(dict(
                name=account.name,
                identifier=account.identifier,
                label='friendly',
                s3_name=account.getCustom('s3_name'),
                s3_canonical_id=account.getCustom('canonical_id')))

        for account in third_party:
            add(cls.OBJECT_STORE['ACCOUNTS'], 'THIRDPARTY', account.identifier)
            cls.OBJECT_STORE['ACCOUNTS']['DESCRIPTIONS'].append(dict(
                name=account.name,
                identifier=account.identifier,
                label='thirdparty',
                s3_name=account.getCustom('s3_name'),
                s3_canonical_id=account.getCustom('canonical_id')))

    @staticmethod
    def _load_related_items(technology_name):
        query = Item.query.join((Technology, Technology.id == Item.tech_id))
        query = query.filter(Technology.name==technology_name)
        return query.all()

    def _get_account(self, key, value):
        """ _get_account('s3_name', 'blah') """
        if key == 'aws':
            return dict(name='AWS', identifier='AWS')
        for account in self.OBJECT_STORE['ACCOUNTS']['DESCRIPTIONS']:
            if unicode(account.get(key, '')).lower() == value.lower():
                return account

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
