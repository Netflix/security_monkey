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
.. module: security_monkey.views.tech_methods
    :platform: Unix

.. version:: $$VERSION$$
.. moduleauthor:: Bridgewater OSS <opensource@bwater.com>


"""
from security_monkey.views import AuthenticatedService
from security_monkey.auditor import auditor_registry
from security_monkey import rbac


class TechMethodsGet(AuthenticatedService):
    decorators = [
        rbac.allow(["View"], ["GET"]),
    ]

    def __init__(self):
        super(TechMethodsGet, self).__init__()

    def get(self, tech_ids):
        """
            .. http:get:: /api/1/techmethods

            Get a list of technologies and associated auditor check methods

            **Example Request**:

            .. sourcecode:: http

                GET /api/1/techmethods HTTP/1.1
                Host: example.com
                Accept: application/json, text/javascript

            **Example Response**:

            .. sourcecode:: http

                HTTP/1.1 200 OK
                Vary: Accept
                Content-Type: application/json

                {
                    "technologies": [ "subnet" ]
                    "tech_methods": { "subnet": [ "check_internet_access" ] }
                    auth: {
                        authenticated: true,
                        user: "user@example.com"
                    }
                }

            :statuscode 200: no error
            :statuscode 401: Authentication failure. Please login.
        """
        tech_methods = {}

        for key in list(auditor_registry.keys()):
            methods = []

            for auditor_class in auditor_registry[key]:
                auditor = auditor_class('')
                for method_name in dir(auditor):
                    method_name = method_name + ' (' + auditor.__class__.__name__ + ')'
                    if (method_name.find("check_")) == 0:
                        methods.append(method_name)

                tech_methods[key] = methods

        marshaled_dict = {
            'tech_methods': tech_methods,
            'auth': self.auth_dict
        }

        return marshaled_dict, 200
