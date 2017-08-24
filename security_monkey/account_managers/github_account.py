#     Copyright 2017 Netflix
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
.. module: security_monkey.accounts.github_account
    :platform: Unix
    :synopsis: Manages GitHub Organizations.


.. version:: $$VERSION$$
.. moduleauthor:: Mike Grima <mgrima@netflix.com>


"""
from security_monkey.account_manager import AccountManager, CustomFieldConfig


class GitHubAccountManager(AccountManager):
    account_type = 'GitHub'
    identifier_label = 'Organization Name'
    identifier_tool_tip = 'Enter the GitHub Organization Name'
    access_token_tool_tip = "Enter the path to the file that contains the GitHub personal access token."
    custom_field_configs = [
        CustomFieldConfig('access_token_file', "Personal Access Token", True, access_token_tool_tip),
    ]

    def __init__(self):
        super(GitHubAccountManager, self).__init__()
