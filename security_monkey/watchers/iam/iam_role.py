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
from joblib import Parallel, delayed
from botor.aws.iam import get_role_inline_policies
from botor.aws.iam import get_role_instance_profiles
from botor.aws.iam import get_role_managed_policies
from botor.aws.iam import list_roles
from security_monkey.decorators import record_exception, iter_account_region
from security_monkey.watcher import ChangeItem
from security_monkey.watcher import Watcher
from security_monkey import app


def _basic_config(role):
    return {
        'role': {
            'path': role.get('Path'),
            'role_name': role.get('RoleName'),
            'create_date': role.get('CreateDate').strftime('%Y-%m-%dT%H:%M:%SZ'),
            'arn': role.get('Arn'),
            'role_id': role.get('RoleId')
        },
        'assume_role_policy_document': role.get('AssumeRolePolicyDocument')
    }


@record_exception()
def process_role(role, **kwargs):
    app.logger.debug("Slurping {index} ({name}) from {account}".format(
        index=IAMRole.i_am_singular,
        name=kwargs['name'],
        account=kwargs['account_name'])
    )
    config = _basic_config(role)

    config.update(
        {
            'managed_policies': get_role_managed_policies(role, **kwargs),
            'rolepolicies': get_role_inline_policies(role, **kwargs),
            'instance_profiles': get_role_instance_profiles(role, **kwargs)
        }
    )

    return config


class IAMRole(Watcher):
    index = 'iamrole'
    i_am_singular = 'IAM Role'
    i_am_plural = 'IAM Roles'

    def __init__(self, accounts=None, debug=False):
        super(IAMRole, self).__init__(accounts=accounts, debug=debug)

    @record_exception()
    def list_roles(self, **kwargs):
        roles = list_roles(**kwargs)
        return [role for role in roles if not self.check_ignore_list(role['RoleName'])]

    def slurp(self):
        self.prep_for_slurp()

        @iter_account_region(index=self.index, accounts=self.accounts, regions=['us-east-1'])
        def slurp_items(**kwargs):
            item_list = []
            exception_map = {}
            kwargs['exception_map'] = exception_map
            kwargs['exception_record_region'] = 'universal'
            roles = self.list_roles(**kwargs)

            roles = zip(
                [role['RoleName'] for role in roles],
                Parallel(n_jobs=2, backend="threading")(
                    delayed(process_role)
                    (role, name=role['RoleName'], **kwargs)
                    for role in roles
                )
            )
            for role in roles:
                item = IAMRoleItem(account=kwargs['account_name'], name=role[0], config=role[1])
                item_list.append(item)

            return item_list, exception_map
        return slurp_items()


class IAMRoleItem(ChangeItem):
    def __init__(self, account=None, name=None, config={}):
        super(IAMRoleItem, self).__init__(
            index=IAMRole.index,
            region='universal',
            account=account,
            name=name,
            new_config=config)
