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
.. module: security_monkey.watchers.iam.iam_role
    :platform: Unix

.. version:: $$VERSION$$
.. moduleauthor:: Patrick Kelley <pkelley@netflix.com> @monkeysecurity

"""

from security_monkey.watcher import Watcher
from security_monkey.watcher import ChangeItem
from security_monkey.exceptions import BotoConnectionIssue
from security_monkey.exceptions import AWSRateLimitReached
from boto.exception import BotoServerError
from security_monkey import app

import json
import urllib


def all_managed_policies(conn):
    managed_policies = {}

    for policy in conn.policies.all():
        for attached_role in policy.attached_roles.all():
            policy = {
                "name": policy.policy_name,
                "arn": policy.arn,
                "version": policy.default_version_id
            }

            if attached_role.arn not in managed_policies:
                managed_policies[attached_role.arn] = [policy]
            else:
                managed_policies[attached_role.arn].append(policy)

    return managed_policies


class IAMRole(Watcher):
    index = 'iamrole'
    i_am_singular = 'IAM Role'
    i_am_plural = 'IAM Roles'

    def __init__(self, accounts=None, debug=False):
        super(IAMRole, self).__init__(accounts=accounts, debug=debug)

    def instance_profiles_for_role(self, iam, role):
        marker = None
        all_instance_profiles =[]
        while True:
            instance_profiles = self.wrap_aws_rate_limited_call(
                iam.list_instance_profiles_for_role,
                role.role_name,
                marker=marker
            )
            all_instance_profiles.extend(instance_profiles.instance_profiles)
            if instance_profiles.is_truncated == u'true':
                marker = instance_profiles.marker
            else:
                break

        return all_instance_profiles

    def policy_names_for_role(self, iam, role):
        marker = None
        all_policy_names =[]
        while True:
            policynames_response = self.wrap_aws_rate_limited_call(
                iam.list_role_policies,
                role.role_name,
                marker=marker
            )
            all_policy_names.extend(policynames_response.policy_names)

            if policynames_response.is_truncated == u'true':
                marker = policynames_response.marker
            else:
                break

        return all_policy_names

    def slurp(self):
        """
        :returns: item_list - list of IAM Roles.
        :returns: exception_map - A dict where the keys are a tuple containing the
            location of the exception and the value is the actual exception
        """
        self.prep_for_slurp()

        item_list = []
        exception_map = {}
        from security_monkey.common.sts_connect import connect
        for account in self.accounts:
            try:
                iam_b3 = connect(account, 'iam_boto3')
                managed_policies = all_managed_policies(iam_b3)

                iam = connect(account, 'iam')
                all_roles = []
                marker = None
                while True:
                    roles = self.wrap_aws_rate_limited_call(iam.list_roles, marker=marker)
                    all_roles.extend(roles.roles)
                    if roles.is_truncated == u'true':
                        marker = roles.marker
                    else:
                        break

            except Exception as e:
                # Some Accounts don't subscribe to EC2 and will throw an exception here.
                exc = BotoConnectionIssue(str(e), 'iamrole', account, None)
                self.slurp_exception((self.index, account, 'universal'), exc, exception_map)
                continue

            for role in all_roles:
                item_config = {}

                app.logger.debug("Slurping %s (%s) from %s" % (self.i_am_singular, role.role_name, account))

                if self.check_ignore_list(role.role_name):
                    continue

                if managed_policies.has_key(role.arn):
                    item_config['managed_policies'] = managed_policies.get(role.arn)

                assume_role_policy_document = role.get('assume_role_policy_document', '')
                assume_role_policy_document = urllib.unquote(assume_role_policy_document)
                assume_role_policy_document = json.loads(assume_role_policy_document)
                item_config['assume_role_policy_document'] = assume_role_policy_document

                del role['assume_role_policy_document']
                item_config['role'] = dict(role)

                instance_profiles = self.instance_profiles_for_role(iam, role)
                if len(instance_profiles) > 0:
                    item_config['instance_profiles'] = []
                    for instance_profile in instance_profiles:
                        del instance_profile['roles']
                        item_config['instance_profiles'].append(dict(instance_profile))

                item_config['rolepolicies'] = {}
                for policy_name in self.policy_names_for_role(iam, role):
                    policy_response = self.wrap_aws_rate_limited_call(
                        iam.get_role_policy,
                        role.role_name,
                        policy_name
                    )
                    policy = policy_response.policy_document
                    policy = urllib.unquote(policy)
                    policy = json.loads(policy)
                    item_config['rolepolicies'][policy_name] = policy

                item = IAMRoleItem(account=account, name=role.role_name, config=item_config)
                item_list.append(item)
        return item_list, exception_map


class IAMRoleItem(ChangeItem):
    def __init__(self, account=None, name=None, config={}):
        super(IAMRoleItem, self).__init__(
            index=IAMRole.index,
            region='universal',
            account=account,
            name=name,
            new_config=config)
