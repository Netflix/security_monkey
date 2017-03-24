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
.. moduleauthor:: Mike Grima <mgrima@netflix.com>
.. moduleauthor:: Patrick Kelley <pkelley@netflix.com> @monkeysecurity

"""
from cloudaux.orchestration.aws.iam.role import get_role
from cloudaux.aws.iam import list_roles
from cloudaux.decorators import iter_account_region

from security_monkey.decorators import record_exception
from security_monkey.watcher import ChangeItem
from security_monkey.watcher import Watcher
from security_monkey import app


class IAMRole(Watcher):
    index = 'iamrole'
    i_am_singular = 'IAM Role'
    i_am_plural = 'IAM Roles'

    def __init__(self, accounts=None, debug=False):
        super(IAMRole, self).__init__(accounts=accounts, debug=debug)

        self.batched_size = 100
        self.done_slurping = False
        self.next_role = 0

    @record_exception(source="iamrole-watcher", pop_exception_fields=True)
    def list_roles(self, **kwargs):
        roles = list_roles(**kwargs["conn_dict"])
        return [role for role in roles if not self.check_ignore_list(role['RoleName'])]

    @record_exception(source="iamrole-watcher", pop_exception_fields=True)
    def process_role(self, role, **kwargs):
        app.logger.debug("Slurping {index} ({name}) from {account}/{region}".format(
            index=self.i_am_singular,
            name=role['RoleName'],
            account=kwargs["conn_dict"]["account_number"],
            region=kwargs["conn_dict"]["region"]))

        # Need to send a copy, since we don't want to alter the total list!
        return get_role(dict(role), **kwargs["conn_dict"])

    def slurp_list(self):
        self.prep_for_batch_slurp()
        exception_map = {}

        @iter_account_region("iam", accounts=[self.current_account[0].identifier], session_name="SecurityMonkey",
                             assume_role=self.current_account[0].getCustom("role_name") or 'SecurityMonkey',
                             regions=["us-east-1"], conn_type="dict")
        def get_role_list(**kwargs):
            app.logger.debug("Fetching the full list of {index} that need to be slurped from {account}"
                             "/{region}...".format(index=self.i_am_plural,
                                                   account=self.current_account[0].name,
                                                   region=kwargs["conn_dict"]["region"]))
            roles = self.list_roles(index=self.index, exception_record_region="universal",
                                    account_name=self.current_account[0].name,
                                    exception_map=exception_map,
                                    **kwargs)

            # Are there any roles?
            if not roles:
                self.done_slurping = True
                roles = []

            return roles

        for r in get_role_list():
            self.total_list.extend(r)

        return exception_map

    def slurp(self):
        exception_map = {}
        batched_items = []

        @iter_account_region("iam", accounts=[self.current_account[0].identifier], session_name="SecurityMonkey",
                             assume_role=self.current_account[0].getCustom("role_name") or 'SecurityMonkey',
                             regions=["us-east-1"], conn_type="dict")
        def slurp_items(**kwargs):
            item_list = []  # Only one region, so just keeping in iter_account_region...

            # This sets the role counting index -- which will then be incremented as things progress...
            role_counter = self.batch_counter * self.batched_size
            while self.batched_size - len(item_list) > 0 and not self.done_slurping:
                current_role = self.total_list[role_counter]
                role = self.process_role(current_role, name=current_role["RoleName"],
                                         index=self.index, exception_record_region="universal",
                                         account_name=self.current_account[0].name,
                                         exception_map=exception_map,
                                         **kwargs)
                if role:
                    item = IAMRoleItem.from_slurp(role, account_name=self.current_account[0].name, **kwargs)
                    item_list.append(item)

                # If an exception is encountered -- skip the role for now...
                role_counter += 1

                # Are we done yet?
                if role_counter == len(self.total_list):
                    self.done_slurping = True

            self.batch_counter += 1

            return item_list

        for r in slurp_items():
            batched_items.extend(r)

        return batched_items, exception_map


class IAMRoleItem(ChangeItem):
    def __init__(self, account=None, name=None, arn=None, config=None):
        config = config or {}

        super(IAMRoleItem, self).__init__(
            index=IAMRole.index,
            region='universal',
            account=account,
            name=name,
            arn=arn,
            new_config=config)

    @classmethod
    def from_slurp(cls, role, **kwargs):
        return cls(
            account=kwargs['account_name'],
            name=role['RoleName'],
            config=role,
            arn=role['Arn'])
