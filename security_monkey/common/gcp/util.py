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
.. module: security_monkey.common.gcp.util
    :platform: Unix

.. version:: $$VERSION$$
.. moduleauthor:: Tom Melendez <supertom@google.com> @supertom
"""
from security_monkey.datastore import Account
from cloudaux.orchestration import modify as cloudaux_modify


def get_gcp_project_creds(account_names):
    """
    Build list of dicts with project credentials.

    Takes a list of account names and fetches all of those accounts.
    If the custom_field 'credentials_file' (custom field) is set, the list
    item will be in the format of: {'project': 'my-project', 'key_file': 'my-key'}
    Otherwise, it will be simply the project string.

    Returns a list containing strings or dictionaries with necessary credentials
    for connecting to GCP.

    :param account_names: list of account names
    :type account_names: ``list``

    :return: list of dictionaries with project credentials
    :rtype: ``list``
    """
    # The name of the field as defined in the GCP Account Manager.
    creds_field = 'creds_file'
    project_creds = []

    accounts = Account.query.filter(Account.name.in_(account_names)).all()

    for account in accounts:
        key_file = account.getCustom(creds_field)
        if key_file:
            project_creds.append({'project': account.identifier, 'key_file': key_file})
        else:
            project_creds.append(account.identifier)

    return project_creds


def gcp_resource_id_builder(service, identifier, project_id, region=''):
    resource = 'gcp:%s:%s:%s:%s' % (project_id, region, service, identifier)
    return resource.replace('/', ':').replace('.', ':')


def modify(d, output='camelized'):
    return cloudaux_modify(d, output=output)


def get_user_agent(**kwargs):
    from security_monkey.common.gcp.config import ApplicationConfig as appconfig
    return 'security-monkey/%s' % appconfig.get_version()
