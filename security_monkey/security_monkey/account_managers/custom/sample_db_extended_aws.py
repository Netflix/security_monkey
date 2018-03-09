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
.. module: security_monkey.accounts.sample_extended_aws
    :platform: Unix
    :synopsis: Extends an AWS account with additional qualifiers that may be
    used to in the applied_to_account method in custom auditors


.. version:: $$VERSION$$
.. moduleauthor:: Bridgewater OSS <opensource@bwater.com>


"""
# from security_monkey.account_manager import CustomFieldConfig
# from security_monkey.account_managers.aws_account import AWSAccountManager
# from security_monkey.datastore import Account, AccountTypeCustomValues
# from security_monkey import app
#
#
# class DBExtendedAWSAccountManager(AWSAccountManager):
#     account_type = 'DB_EXTENDED_AWS'
#     compatable_account_types = ['AWS']
#     custom_field_configs = AWSAccountManager.custom_field_configs + [
#         CustomFieldConfig('security_level', 'Security Level', True,
#             'A numeric value used to indicated the risk'),
#     ]
#
#     def __init__(self):
#         super(ExtendedAWSAccountManager, self).__init__()
