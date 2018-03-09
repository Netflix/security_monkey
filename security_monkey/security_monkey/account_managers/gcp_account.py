#     Copyright 2017 Google Inc.
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
.. module: security_monkey.accounts.gcp_account
    :platform: Unix
    :synopsis: Manages generic GCP account.


.. version:: $$VERSION$$
.. moduleauthor:: Tom Melendez (@supertom) <supertom@google.com>


"""
from security_monkey.account_manager import AccountManager, CustomFieldConfig
from security_monkey.datastore import Account


class GCPAccountManager(AccountManager):
    account_type = 'GCP'
    identifier_label = 'Project ID'
    identifier_tool_tip = 'Enter the GCP Project ID.'
    creds_file_tool_tip = 'Enter the path on disk to the credentials file.'
    custom_field_configs = [
        CustomFieldConfig('creds_file', 'Credentials File', True, creds_file_tool_tip),
    ]

    def __init__(self):
        super(GCPAccountManager, self).__init__()

    def lookup_account_by_identifier(self, identifier):
        """
        Overrides the lookup to also check the number for backwards compatibility
        """
        account = super(GCPAccountManager,
                        self).lookup_account_by_identifier(identifier)
        return account

    def _populate_account(self, account, account_type, name, active, third_party,
                          notes, identifier, custom_fields=None):
        """
        # TODO(supertom): look into this.
        Overrides create and update to also save the number, s3_name and role_name
        for backwards compatibility
        """
        account = super(GCPAccountManager, self)._populate_account(account, account_type, name, active, third_party,
                                                                   notes, identifier, custom_fields)

        return account
