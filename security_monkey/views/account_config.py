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
.. module: security_monkey.views.account_config
    :platform: Unix
    :synopsis: Manages generic AWS account.


.. version:: $$VERSION$$
.. moduleauthor:: Bridgewater OSS <opensource@bwater.com>


"""

from security_monkey.views import AuthenticatedService
from security_monkey.datastore import AccountType
from security_monkey.account_manager import account_registry, load_all_account_types
from security_monkey import rbac

from flask_restful import reqparse

class AccountConfigGet(AuthenticatedService):
    decorators = [
        rbac.allow(["View"], ["GET"]),
    ]

    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        super(AccountConfigGet, self).__init__()

    def get(self, account_fields):
        """
            .. http:get:: /api/1/account_config/account_fields (all or custom)

            Get a list of Account types

            **Example Request**:

            .. sourcecode:: http

                GET /api/1/account_config/all HTTP/1.1
                Host: example.com
                Accept: application/json, text/javascript

            **Example Response**:

            .. sourcecode:: http

                HTTP/1.1 200 OK
                Vary: Accept
                Content-Type: application/json

                {
                    auth: {
                        authenticated: true,
                        user: "user@example.com"
                    }
                }

            :statuscode 200: no error
            :statuscode 401: Authentication failure. Please login.
        """
        load_all_account_types()
        marshaled = {}
        account_types = AccountType.query.all()
        configs_marshaled = {}

        for account_type in account_types:
            acc_manager = account_registry.get(account_type.name)
            if acc_manager is not None:
                values = {}
                values['identifier_label'] = acc_manager.identifier_label
                values['identifier_tool_tip'] = acc_manager.identifier_tool_tip
                fields = []

                if account_fields == 'all':
                    fields.append({ 'name': 'identifier',
                                    'label': '',
                                    'editable': True,
                                    'tool_tip': '',
                                    'password': False,
                                    'allowed_values': None
                                  }
                    )

                    fields.append({ 'name': 'name',
                                    'label': '',
                                    'editable': True,
                                    'tool_tip': '',
                                    'password': False,
                                    'allowed_values': None
                                  }
                    )

                    fields.append({ 'name': 'notes',
                                    'label': '',
                                    'editable': True,
                                    'tool_tip': '',
                                    'password': False,
                                    'allowed_values': None
                                  }
                    )

                for config in acc_manager.custom_field_configs:
                    if account_fields == 'custom' or not config.password:
                        field_marshaled = {
                            'name': config.name,
                            'label': config.label,
                            'editable': config.db_item,
                            'tool_tip': config.tool_tip,
                            'password': config.password,
                            'allowed_values': config.allowed_values
                        }
                        fields.append(field_marshaled)

                    values['fields'] = fields
                configs_marshaled[account_type.name] = values

        marshaled['custom_configs'] = configs_marshaled
        marshaled['auth'] = self.auth_dict

        return marshaled, 200
