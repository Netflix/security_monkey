#     Copyright 2016 Bridgewater Associates
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
.. module: security_monkey.accounts.sample_active_directory
    :platform: Unix
    :synopsis: Manages Active Directory account. Adds fields needed to connect
    as custom fields

.. version:: $$VERSION$$
.. moduleauthor:: Bridgewater OSS <opensource@bwater.com>


"""
# from security_monkey.account_manager import AccountManager, CustomFieldConfig
#
# class ActiveDirectoryAccountManager(AccountManager):
#     account_type = 'ACTIVE_DIRECTORY'
#     identifier_label = 'URL'
#     identifier_tool_tip = 'Enter the URL of the active directory account'
#     custom_field_configs = [
#         CustomFieldConfig('user_id', 'User ID', True,
#             'Enter the user id for the account'),
#         CustomFieldConfig('password', 'Password', True,
#             "Enter the user's password to access the account", True)
#     ]
#
#     def __init__(self):
#         super(AccountManager, self).__init__()
