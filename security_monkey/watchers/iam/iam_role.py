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
from cloudaux.orchestration.aws.iam.role import get_role
from cloudaux.aws.iam import list_roles
from security_monkey.decorators import record_exception, iter_account_region
from security_monkey.watcher import ChangeItem
from security_monkey.watcher import Watcher
from security_monkey import app


class IAMRole(Watcher):
    index = 'iamrole'
    i_am_singular = 'IAM Role'
    i_am_plural = 'IAM Roles'

    def __init__(self, accounts=None, debug=False):
        super(IAMRole, self).__init__(accounts=accounts, debug=debug)

    @record_exception(source="iamrole-watcher")
    def list_roles(self, **kwargs):
        roles = list_roles(**kwargs)
        return [role for role in roles if not self.check_ignore_list(role['RoleName'])]

    @record_exception(source="iamrole-watcher")
    def process_role(self, role, **kwargs):
        app.logger.debug("Slurping {index} ({name}) from {account}".format(
            index=self.i_am_singular,
            name=kwargs['name'],
            account=kwargs['account_name']))
        return get_role(role, **kwargs)

    def cast_to_item(self, role, **kwargs):
        return IAMRoleItem(
            account=kwargs['account_name'],
            name=role['RoleName'],
            config=role,
            arn=role['Arn'])

    def slurp(self):
        self.prep_for_slurp()

        @iter_account_region(index=self.index, accounts=self.accounts, exception_record_region='universal')
        def slurp_items(**kwargs):
            item_list = []
            roles = self.list_roles(**kwargs)

            for role in roles:
                role = self.process_role(role, name=role['RoleName'], **kwargs)
                item = self.cast_to_item(role, **kwargs)
                item_list.append(item)

            return item_list, kwargs.get('exception_map', {})
        return slurp_items()


class IAMRoleItem(ChangeItem):
    def __init__(self, account=None, name=None, arn=None, config={}):
        super(IAMRoleItem, self).__init__(
            index=IAMRole.index,
            region='universal',
            account=account,
            name=name,
            arn=arn,
            new_config=config)
