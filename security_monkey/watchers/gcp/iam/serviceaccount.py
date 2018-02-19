#     Copyright 2017 Google, Inc.
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
.. module: security_monkey.watchers.gcp.iam.serviceaccount
    :platform: Unix

.. version:: $$VERSION$$
.. moduleauthor:: Tom Melendez <supertom@google.com> @supertom

"""
from security_monkey.common.gcp.util import get_gcp_project_creds, get_user_agent, gcp_resource_id_builder
from security_monkey.decorators import record_exception
from security_monkey.watcher import Watcher
from security_monkey.watcher import ChangeItem

from cloudaux.gcp.decorators import iter_project
from cloudaux.gcp.iam import list_serviceaccounts
from cloudaux.orchestration.gcp.iam.serviceaccount import get_serviceaccount_complete


class IAMServiceAccount(Watcher):
    index = 'iamserviceaccount'
    i_am_singular = 'IAMServiceAccount'
    i_am_plural = 'IAMServiceAccounts'
    account_type = 'GCP'

    def __init__(self, accounts=None, debug=False):
        super(IAMServiceAccount, self).__init__(accounts=accounts, debug=debug)
        self.honor_ephemerals = True
        self.ephemeral_paths = [
            "Etag",
        ]
        self.user_agent = get_user_agent()

    @record_exception()
    def slurp(self):
        """
        :returns: item_list - list of IAMServiceAccounts.
        :returns: exception _map - A dict where the keys are a tuple containing the
        location of the exception and the value is the actual exception
        """
        self.prep_for_slurp()

        project_creds = get_gcp_project_creds(self.accounts)

        @iter_project(projects=project_creds)
        def slurp_items(**kwargs):
            item_list = []
            kwargs['user_agent'] = self.user_agent
            service_accounts = list_serviceaccounts(**kwargs)

            for service_account in service_accounts:
                resource_id = gcp_resource_id_builder(
                    kwargs['project'], 'projects.serviceaccounts.get', service_account['name'])
                sa = get_serviceaccount_complete(
                    service_account=service_account['name'], **kwargs)

                key_count = 0
                if 'Keys' in sa:
                    key_count = len(sa['Keys'])

                item_list.append(
                    IAMServiceAccountItem(
                        region='global',
                        # This should only ever be the first item (shouldn't make this a list)
                        account=self.accounts[0],
                        name=sa['Email'],
                        arn=resource_id,
                        config={
                            'policy': sa.get('Policy', None),
                            'email': sa['Email'],
                            'keys': key_count,
                        }))
            return item_list, kwargs.get('exception_map', {})

        return slurp_items()


class IAMServiceAccountItem(ChangeItem):

    def __init__(self,
                 region=None,
                 account=None,
                 name=None,
                 arn=None,
                 config=None):
        if config is None:
            config = {}
        super(IAMServiceAccountItem, self).__init__(
            index=IAMServiceAccount.index,
            region=region,
            account=account,
            name=name,
            arn=arn,
            new_config=config)
