#     Copyright 2014 Netflix, Inc.
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
.. module: security_monkey.backup
    :platform: Unix

.. version:: $$VERSION$$
.. moduleauthor:: Patrick Kelley <pkelley@netflix.com> @monkeysecurity

"""
from security_monkey.monitors import get_monitors
from security_monkey.datastore import Item, ItemRevision, Account, Technology
import json
import os


def backup_config_to_json(account_names, monitor_names, output_folder):
    for account_name in account_names:
        monitors = get_monitors(account_name, monitor_names)
        for monitor in monitors:
            _backup_items_in_account(account_name, monitor.watcher, output_folder)


def _backup_items_in_account(account_name, watcher, output_folder):
    technology_name = watcher.index
    query = Item.query
    query = query.join((Account, Account.id==Item.account_id))
    query = query.join((Technology, Technology.id==Item.tech_id))
    query = query.filter(Account.name == account_name)
    query = query.filter(Technology.name == technology_name)
    items_to_backup = query.all()

    for item in items_to_backup:
        latest_revision = ItemRevision.query.filter(ItemRevision.id==item.latest_revision_id).first()
        _serialize_item_to_file(item, latest_revision, output_folder, account_name, technology_name)


def standardize_name(name):
    """Some objects have a / in their names.  This allows the backup to proceed.
     Further sanitization would be wise with untrusted input."""
    return name.replace('/', '_') if name else 'no_name.json'


def _serialize_item_to_file(item, latest_revision, output_folder, account_name, technology_name):
    output_folder = "{0}/{1}/{2}".format(
        output_folder,
        account_name,
        technology_name
    )
    if not os.path.isdir(output_folder):
        os.makedirs(output_folder, mode=0o777)
    output_file = "{0}/{1}.json".format(
        output_folder,
        standardize_name(item.name)
    )
    print(("Writing {0} to {1}".format(item.name, output_file)))
    with open(output_file, 'w') as output:
        output.write(json.dumps(latest_revision.config, indent=2))
