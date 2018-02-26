#     Copyright (c) 2017 AT&T Intellectual Property. All rights reserved.
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
.. module: security_monkey.accounts.openstack_account
    :platform: Unix
    :synopsis: Manages generic OpenStack account.


.. version:: $$VERSION$$
.. moduleauthor:: Michael Stair <mstair@att.com>


"""
from security_monkey.account_manager import AccountManager, CustomFieldConfig
from security_monkey.datastore import Account


class OpenStackAccountManager(AccountManager):
    account_type = 'OpenStack'
    identifier_label = 'Cloud Name'
    identifier_tool_tip = 'OpenStack Cloud Name. Cloud configuration to load from clouds.yaml file'

    cloudsyaml_tool_tip = ('Path on disk to clouds.yaml file')
    custom_field_configs = [        
        CustomFieldConfig('cloudsyaml_file', 'OpenStack clouds.yaml file', True, cloudsyaml_tool_tip)
    ]

    def __init__(self):
        super(OpenStackAccountManager, self).__init__()
