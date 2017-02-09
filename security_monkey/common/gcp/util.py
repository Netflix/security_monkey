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
.. module: security_monkey.watchers.gcp.util
    :platform: Unix

.. version:: $$VERSION$$
.. moduleauthor:: Tom Melendez <supertom@google.com> @supertom
"""
from security_monkey.datastore import Account
from cloudaux.orchestration import modify as cloudaux_modify


def identifiers_from_account_names(account_names):
    accounts = Account.query.filter(Account.name.in_(account_names)).all()
    return [account.identifier for account in accounts]


def gcp_resource_id_builder(service, identifier, region=''):
    resource = 'gcp:%s:%s:%s' % (region, service, identifier)
    return resource.replace('/', ':').replace('.', ':')


def modify(d, format='camelized'):
    return cloudaux_modify(d, format=format)
