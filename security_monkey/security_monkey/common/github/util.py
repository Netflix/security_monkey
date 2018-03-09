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
.. module: security_monkey.common.github.util
    :platform: Unix
    :synopsis: Utility functions for Security Monkey's GitHub Organization Plugin.


.. version:: $$VERSION$$
.. moduleauthor:: Mike Grima <mgrima@netflix.com>

"""
import json
from functools import wraps

from security_monkey import app
from security_monkey.datastore import Account
from security_monkey.exceptions import GitHubCredsError


def get_github_creds(account_names):
    """
    Grab GitHub credentials from a JSON file on disk.

    The dict looks like this:
    {
        "Organization-Name": "API KEY",
        "Organization-Name-2": "API KEY 2",
        ...
    }

    :param account_names: list of account names
    :type account_names: ``list``
    """
    # The name of the field as defined in the GitHub Account Manager.
    creds_field = 'access_token_file'
    org_creds = {}

    accounts = Account.query.filter(Account.name.in_(account_names)).all()

    for account in accounts:
        try:
            if not org_creds.get(account.identifier):
                creds_file = account.getCustom(creds_field)
                if creds_file:
                    with open(creds_file, "r") as file:
                        creds_dict = json.loads(file.read())

                    org_creds.update(creds_dict)
                else:
                    org_creds.update(app.config.get("GITHUB_CREDENTIALS"))
        except Exception as _:
            raise GitHubCredsError(account.identifier)

    return org_creds


def iter_org(orgs):
    """
    Decorator for looping over many GitHub organizations.

    This will pass in the exception map properly.
    :param orgs:
    :return:
    """
    def decorator(func):
        @wraps(func)
        def decorated_function(*args, **kwargs):
            item_list = []
            if not kwargs.get("exception_map"):
                kwargs["exception_map"] = {}

            for org in orgs:
                kwargs["account_name"] = org
                item, exc = func(*args, **kwargs)
                item_list.extend(item)

            return item_list, kwargs["exception_map"]

        return decorated_function

    return decorator


def strip_url_fields(blob):
    """
    Utility function to strip out the "_url" fields returned from GitHub, since
    they aren't really useful for the purposes of Security Monkey, and add in
    bloat to the record.

    This will recursively remove them from nested dictionaries.
    :param blob:
    :return:
    """
    keys_to_delete = []

    if isinstance(blob, list):
        for item in blob:
            strip_url_fields(item)
    if not isinstance(blob, dict):
        return blob

    for k in blob:
        # Is the field a dictionary or list of dicts?
        if isinstance(blob[k], dict) or isinstance(blob[k], list):
            strip_url_fields(blob[k])

        if "_url" in k:
            keys_to_delete.append(k)

    # Delete them:
    for k in keys_to_delete:
        del blob[k]

    return blob
