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
.. module: security_monkey.tests.core.test_backup
    :platform: Unix

.. version:: $$VERSION$$
.. moduleauthor:: Bridgewater OSS <opensource@bwater.com>

"""
from security_monkey.datastore import Account, AccountType
from security_monkey.tests import SecurityMonkeyTestCase
from security_monkey.tests.core.monitor_mock import build_mock_result, mock_get_monitors
from security_monkey import db

from mock import patch
from collections import defaultdict


watcher_configs = [
    {'index': 'index1', 'interval': 15},
    {'index': 'index2', 'interval': 15},
    {'index': 'index3', 'interval': 15}
]

mock_file_system = defaultdict(list)


def mock_backup_items_in_account(account_name, watcher, output_folder):
    mock_file_system[account_name].append(watcher.index)


@patch('security_monkey.backup._backup_items_in_account', mock_backup_items_in_account)
@patch('security_monkey.monitors.get_monitors', mock_get_monitors)
class BackupTestCase(SecurityMonkeyTestCase):

    def pre_test_setup(self):
        account_type_result = AccountType(name='AWS')
        db.session.add(account_type_result)
        db.session.commit()

        account = Account(identifier="012345678910", name="TEST_ACCOUNT",
                          account_type_id=account_type_result.id, notes="TEST_ACCOUNT",
                          third_party=False, active=True)

        db.session.add(account)
        db.session.commit()

        mock_file_system.clear()
        build_mock_result(watcher_configs, [])

    def tearDown(self):
        import security_monkey.auditor
        security_monkey.auditor.auditor_registry = defaultdict(list)
        super(BackupTestCase, self).tearDown()

    def test_backup_with_all_watchers(self):
        from security_monkey.backup import backup_config_to_json

        backup_config_to_json(['TEST_ACCOUNT'], ['index1', 'index2', 'index3'], 'none')

        self.assertTrue('TEST_ACCOUNT' in list(mock_file_system.keys()),
                        msg="Did not backup TEST_ACCOUNT")
        self.assertEqual(first=1, second=len(list(mock_file_system.keys())),
                         msg="Should backup account once but backed up {} times"
                         .format(len(list(mock_file_system.keys()))))
        self.assertEqual(first=3, second=len(mock_file_system['TEST_ACCOUNT']),
                         msg="Should backup 3 technologies but backed up {}"
                         .format(len(mock_file_system['TEST_ACCOUNT'])))
        self.assertTrue('index1' in mock_file_system['TEST_ACCOUNT'],
                        msg="Did not backup index1")
        self.assertTrue('index2' in mock_file_system['TEST_ACCOUNT'],
                        msg="Did not backup index2")
        self.assertTrue('index3' in mock_file_system['TEST_ACCOUNT'],
                        msg="Did not backup index3")

    def test_backup_with_one_watchers(self):
        from security_monkey.backup import backup_config_to_json

        backup_config_to_json(['TEST_ACCOUNT'], ['index1'], 'none')

        self.assertTrue('TEST_ACCOUNT' in list(mock_file_system.keys()),
                        msg="Did not backup TEST_ACCOUNT")
        self.assertEqual(first=1, second=len(list(mock_file_system.keys())),
                         msg="Should backup account once but backed up {} times"
                         .format(len(list(mock_file_system.keys()))))
        self.assertEqual(first=1, second=len(mock_file_system['TEST_ACCOUNT']),
                         msg="Should backup 1 technologies but backed up {}"
                         .format(len(mock_file_system['TEST_ACCOUNT'])))
        self.assertTrue('index1' in mock_file_system['TEST_ACCOUNT'],
                        msg="Did not backup index1")
