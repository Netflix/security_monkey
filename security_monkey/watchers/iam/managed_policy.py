#     Copyright 2015 Netflix, Inc.
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
.. module: security_monkey.watchers.iam.managed_policy
    :platform: Unix

.. version:: $$VERSION$$
.. moduleauthor:: Patrick Kelley <pkelley@netflix.com> @monkeysecurity

"""

from security_monkey.watcher import Watcher
from security_monkey.watcher import ChangeItem
from security_monkey.exceptions import BotoConnectionIssue
from security_monkey import app, ARN_PREFIX


class ManagedPolicy(Watcher):
    index = 'policy'
    i_am_singular = 'Managed Policy'
    i_am_plural = 'Managed Policies'

    def __init__(self, accounts=None, debug=False):
        super(ManagedPolicy, self).__init__(accounts=accounts, debug=debug)
        self.honor_ephemerals = True
        self.ephemeral_paths = [
            "attached_groups",
            "attached_roles",
            "attached_users",
            "attachment_count"
        ]

    def slurp(self):
        """
        :returns: item_list - list of Managed Policies.
        :returns: exception_map - A dict where the keys are a tuple containing the
            location of the exception and the value is the actual exception
        """
        self.prep_for_slurp()
        item_list = []
        exception_map = {}

        from security_monkey.common.sts_connect import connect
        for account in self.accounts:
            all_policies = []

            try:
                iam = connect(account, 'boto3.iam.resource')

                for policy in iam.policies.all():
                    all_policies.append(policy)

            except Exception as e:
                exc = BotoConnectionIssue(str(e), 'iamuser', account, None)
                self.slurp_exception((self.index, account, 'universal'), exc, exception_map,
                                     source="{}-watcher".format(self.index))
                continue

            for policy in all_policies:

                if self.check_ignore_list(policy.policy_name):
                    continue

                if self.check_ignore_list(policy.arn):
                    continue

                # Skip retrieving attached entities for policies with zero attachments.
                attached_users = []
                attached_roles = []
                attached_groups = []
                if policy.attachment_count > 0:
                    app.logger.debug("Finding attachments for policy %s" % policy.policy_name)
                    attached_users = [a.arn for a in policy.attached_users.all()]
                    attached_roles = [a.arn for a in policy.attached_roles.all()]
                    attached_groups = [a.arn for a in policy.attached_groups.all()]
                else:
                    app.logger.debug("Skipping policy attachment retrieval for policy %s because it has no attachments" % policy.policy_name)

                item_config = {
                    'name': policy.policy_name,
                    'arn': policy.arn,
                    'create_date': str(policy.create_date),
                    'update_date': str(policy.update_date),
                    'default_version_id': policy.default_version_id,
                    'attachment_count': policy.attachment_count,
                    'attached_users': attached_users,
                    'attached_groups': attached_groups,
                    'attached_roles': attached_roles,
                    'policy': policy.default_version.document
                }

                app.logger.debug("Slurping %s (%s) from %s" % (self.i_am_singular, policy.policy_name, account))

                arn = item_config.get('arn')
                # Don't set the ARN field on Amazon owned managed policies as this would violate the
                # unique constraint.  (Unfortunately, security_monkey currently tracks each managed policy
                # as though it exists as a separate entity in each tracked account.)
                if arn.startswith(ARN_PREFIX + ":iam::aws:policy"):
                    arn = None

                item_list.append(
                    ManagedPolicyItem(account=account, name=policy.policy_name, arn=arn, config=item_config,
                                      source_watcher=self)
                )

        return item_list, exception_map


class ManagedPolicyItem(ChangeItem):
    def __init__(self, account=None, name=None, arn=None, config=None, source_watcher=None):
        super(ManagedPolicyItem, self).__init__(
            index=ManagedPolicy.index,
            region='universal',
            account=account,
            name=name,
            arn=arn,
            new_config=config if config else {},
            source_watcher=source_watcher)
