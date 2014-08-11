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
.. module: security_monkey.watchers.iam_role
    :platform: Unix

.. version:: $$VERSION$$
.. moduleauthor:: Patrick Kelley <pkelley@netflix.com> @monkeysecurity

"""

from security_monkey.watcher import Watcher
from security_monkey.watcher import ChangeItem
from security_monkey.exceptions import BotoConnectionIssue
from security_monkey.exceptions import AWSRateLimitReached
from security_monkey.constants import IGNORE_PREFIX
from boto.exception import BotoServerError
from security_monkey import app

import json
import urllib


class IAMRole(Watcher):
    index = 'iamrole'
    i_am_singular = 'IAM Role'
    i_am_plural = 'IAM Roles'

    def __init__(self, accounts=None, debug=False):
        super(IAMRole, self).__init__(accounts=accounts, debug=debug)

    def slurp(self):
        """
        :returns: item_list - list of IAM Roles.
        :returns: exception_map - A dict where the keys are a tuple containing the
            location of the exception and the value is the actual exception
        """
        item_list = []
        exception_map = {}
        from security_monkey.common.sts_connect import connect
        for account in self.accounts:
            try:

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

                ### Check if this Role is on the Ignore List ###
                ignore_item = False
                for ignore_item_name in IGNORE_PREFIX[self.index]:
                    if role.role_name.lower().startswith(ignore_item_name.lower()):
                        ignore_item = True
                        break

                if ignore_item:
                    continue

                assume_role_policy_document = role.get('assume_role_policy_document', '')
                assume_role_policy_document = urllib.unquote(assume_role_policy_document)
                assume_role_policy_document = json.loads(assume_role_policy_document)
                item_config['assume_role_policy_document'] = assume_role_policy_document

                del role['assume_role_policy_document']
                item_config['role'] = dict(role)

                try:
                    # TODO: Also takes a marker
                    policynames_response = self.wrap_aws_rate_limited_call(
                        iam.list_role_policies,
                        role.role_name
                    )
                    policynames = policynames_response.policy_names
                    item_config['rolepolicies'] = {}
                    for policy_name in policynames:
                        policy_response = self.wrap_aws_rate_limited_call(
                            iam.get_role_policy,
                            role.role_name,
                            policy_name
                        )
                        policy = policy_response.policy_document
                        policy = urllib.unquote(policy)
                        policy = json.loads(policy)
                        item_config['rolepolicies'][policy_name] = policy
                except BotoServerError as e:
                    exc = AWSRateLimitReached(str(e), 'iamrole', account, 'universal')
                    self.slurp_exception((self.index, account, 'universal', role.role_name), exc, exception_map)

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
