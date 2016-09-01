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
.. module: security_monkey.tests.test_auditor
    :platform: Unix

.. version:: $$VERSION$$
.. moduleauthor:: Bridgewater OSS <opensource@bwater.com>

"""
from security_monkey.tests import SecurityMonkeyTestCase
from security_monkey.datastore import Account, AccountType
from security_monkey.tests.db_mock import MockAccountQuery, MockDBSession
from security_monkey.tests.monitor_mock import RUNTIME_WATCHERS, RUNTIME_AUDITORS
from security_monkey.tests.monitor_mock import build_mock_result
from security_monkey.tests.monitor_mock import mock_get_monitors, mock_all_monitors

from mock import patch


mock_query = MockAccountQuery()
mock_db_session = MockDBSession()

watcher_configs = [
    {'index': 'index1', 'interval': 15},
    {'index': 'index2', 'interval': 15},
    {'index': 'index3', 'interval': 60}
]


auditor_configs = [
    {
        'index': 'index1',
        'support_auditor_indexes': [],
        'support_watcher_indexes': []
    },
    {
        'index': 'index2',
        'support_auditor_indexes': [],
        'support_watcher_indexes': []
    },
    {
        'index': 'index3',
        'support_auditor_indexes': [],
        'support_watcher_indexes': []
    }
]


@patch('security_monkey.monitors.all_monitors', mock_all_monitors)
@patch('security_monkey.monitors.get_monitors', mock_get_monitors)
class SchedulerTestCase(SecurityMonkeyTestCase):
    test_account1 = None
    test_account2 = None
    test_account3 = None
    test_account4 = None

    def setUp(self):
        mock_query.clear()
        self.test_account1 = Account()
        self.test_account1.name = "TEST_ACCOUNT1"
        self.test_account1.notes = "TEST ACCOUNT1"
        self.test_account1.s3_name = "TEST_ACCOUNT1"
        self.test_account1.number = "012345678910"
        self.test_account1.role_name = "TEST_ACCOUNT"
        self.test_account1.account_type = AccountType(name='AWS')
        self.test_account1.third_party = False
        self.test_account1.active = True
        mock_query.add_account(self.test_account1)

        self.test_account2 = Account()
        self.test_account2.name = "TEST_ACCOUNT2"
        self.test_account2.notes = "TEST ACCOUNT2"
        self.test_account2.s3_name = "TEST_ACCOUNT2"
        self.test_account2.number = "123123123123"
        self.test_account2.role_name = "TEST_ACCOUNT"
        self.test_account2.account_type = AccountType(name='AWS')
        self.test_account2.third_party = False
        self.test_account2.active = True
        mock_query.add_account(self.test_account2)

        self.test_account3 = Account()
        self.test_account3.name = "TEST_ACCOUNT3"
        self.test_account3.notes = "TEST ACCOUNT3"
        self.test_account3.s3_name = "TEST_ACCOUNT3"
        self.test_account3.number = "012345678910"
        self.test_account3.role_name = "TEST_ACCOUNT"
        self.test_account3.account_type = AccountType(name='AWS')
        self.test_account3.third_party = False
        self.test_account3.active = False
        mock_query.add_account(self.test_account3)

        self.test_account4 = Account()
        self.test_account4.name = "TEST_ACCOUNT4"
        self.test_account4.notes = "TEST ACCOUNT4"
        self.test_account4.s3_name = "TEST_ACCOUNT4"
        self.test_account4.number = "123123123123"
        self.test_account4.role_name = "TEST_ACCOUNT"
        self.test_account4.account_type = AccountType(name='AWS')
        self.test_account4.third_party = False
        self.test_account4.active = False
        mock_query.add_account(self.test_account4)

        RUNTIME_WATCHERS.clear()
        RUNTIME_AUDITORS.clear()

    @patch('security_monkey.datastore.Account.query', new=mock_query)
    @patch('security_monkey.db.session.expunge', new=mock_db_session.expunge)
    def test_find_all_changes(self):
        from security_monkey.scheduler import find_changes
        build_mock_result(watcher_configs, auditor_configs)

        find_changes(['TEST_ACCOUNT1', 'TEST_ACCOUNT2'],
                     ['index1', 'index2', 'index3'])

        watcher_keys = RUNTIME_WATCHERS.keys()
        self.assertEqual(first=3, second=len(watcher_keys),
                         msg="Should run 3 watchers but ran {}"
                         .format(len(watcher_keys)))

        self.assertTrue('index1' in watcher_keys,
                        msg="Watcher index1 not run")
        self.assertTrue('index2' in watcher_keys,
                        msg="Watcher index3 not run")
        self.assertTrue('index3' in watcher_keys,
                        msg="Watcher index3 not run")

        self.assertEqual(first=2, second=len(RUNTIME_WATCHERS['index1']),
                         msg="Watcher index1 should run twice but ran {} times"
                         .format(len(RUNTIME_WATCHERS['index1'])))
        self.assertEqual(first=2, second=len(RUNTIME_WATCHERS['index2']),
                         msg="Watcher index2 should run twice but ran {} times"
                         .format(len(RUNTIME_WATCHERS['index2'])))
        self.assertEqual(first=2, second=len(RUNTIME_WATCHERS['index3']),
                         msg="Watcher index2 should run twice but ran {} times"
                         .format(len(RUNTIME_WATCHERS['index3'])))

        auditor_keys = RUNTIME_AUDITORS.keys()
        self.assertEqual(first=3, second=len(auditor_keys),
                         msg="Should run 3 auditors but ran {}"
                         .format(len(auditor_keys)))

        self.assertTrue('index1' in auditor_keys,
                        msg="Auditor index1 not run")
        self.assertTrue('index2' in auditor_keys,
                        msg="Auditor index2 not run")
        self.assertTrue('index3' in auditor_keys,
                        msg="Auditor index3 not run")

        self.assertEqual(first=2, second=len(RUNTIME_AUDITORS['index1']),
                         msg="Auditor index1 should run twice but ran {} times"
                         .format(len(RUNTIME_AUDITORS['index1'])))
        self.assertEqual(first=2, second=len(RUNTIME_AUDITORS['index2']),
                         msg="Auditor index2 should run twice but ran {} times"
                         .format(len(RUNTIME_AUDITORS['index2'])))
        self.assertEqual(first=2, second=len(RUNTIME_AUDITORS['index3']),
                         msg="Auditor index3 should run twice but ran {} times"
                         .format(len(RUNTIME_AUDITORS['index3'])))

    @patch('security_monkey.datastore.Account.query', new=mock_query)
    @patch('security_monkey.db.session.expunge', new=mock_db_session.expunge)
    def test_find_account_changes(self):
        from security_monkey.scheduler import find_changes
        build_mock_result(watcher_configs, auditor_configs)

        find_changes(['TEST_ACCOUNT1'],
                     ['index1', 'index2', 'index3'])

        watcher_keys = RUNTIME_WATCHERS.keys()
        self.assertEqual(first=3, second=len(watcher_keys),
                         msg="Should run 3 watchers but ran {}"
                         .format(len(watcher_keys)))

        self.assertTrue('index1' in watcher_keys,
                        msg="Watcher index1 not run")
        self.assertTrue('index2' in watcher_keys,
                        msg="Watcher index3 not run")
        self.assertTrue('index3' in watcher_keys,
                        msg="Watcher index3 not run")

        self.assertEqual(first=1, second=len(RUNTIME_WATCHERS['index1']),
                         msg="Watcher index1 should run once but ran {} times"
                         .format(len(RUNTIME_WATCHERS['index1'])))
        self.assertEqual(first=1, second=len(RUNTIME_WATCHERS['index2']),
                         msg="Watcher index2 should run once but ran {} times"
                         .format(len(RUNTIME_WATCHERS['index2'])))
        self.assertEqual(first=1, second=len(RUNTIME_WATCHERS['index3']),
                         msg="Watcher index2 should run once but ran {} times"
                         .format(len(RUNTIME_WATCHERS['index3'])))

        auditor_keys = RUNTIME_AUDITORS.keys()
        self.assertEqual(first=3, second=len(auditor_keys),
                         msg="Should run 3 auditors but ran {}"
                         .format(len(auditor_keys)))

        self.assertTrue('index1' in auditor_keys,
                        msg="Auditor index1 not run")
        self.assertTrue('index2' in auditor_keys,
                        msg="Auditor index2 not run")
        self.assertTrue('index3' in auditor_keys,
                        msg="Auditor index3 not run")

        self.assertEqual(first=1, second=len(RUNTIME_AUDITORS['index1']),
                         msg="Auditor index1 should run once but ran {} times"
                         .format(len(RUNTIME_AUDITORS['index1'])))
        self.assertEqual(first=1, second=len(RUNTIME_AUDITORS['index2']),
                         msg="Auditor index2 should run once but ran {} times"
                         .format(len(RUNTIME_AUDITORS['index2'])))
        self.assertEqual(first=1, second=len(RUNTIME_AUDITORS['index3']),
                         msg="Auditor index3 should run once but ran {} times"
                         .format(len(RUNTIME_AUDITORS['index3'])))

    @patch('security_monkey.datastore.Account.query', new=mock_query)
    @patch('security_monkey.db.session.commit', new=mock_db_session.commit)
    def test_disable_all_accounts(self):
        from security_monkey.scheduler import disable_accounts
        disable_accounts(['TEST_ACCOUNT1', 'TEST_ACCOUNT2', 'TEST_ACCOUNT3', 'TEST_ACCOUNT4'])
        self.assertFalse(self.test_account1.active)
        self.assertFalse(self.test_account2.active)
        self.assertFalse(self.test_account3.active)
        self.assertFalse(self.test_account4.active)

    @patch('security_monkey.datastore.Account.query', new=mock_query)
    @patch('security_monkey.db.session.commit', new=mock_db_session.commit)
    def test_disable_one_accounts(self):
        from security_monkey.scheduler import disable_accounts
        disable_accounts(['TEST_ACCOUNT1'])
        self.assertFalse(self.test_account1.active)
        self.assertTrue(self.test_account2.active)
        self.assertFalse(self.test_account3.active)
        self.assertFalse(self.test_account4.active)

    @patch('security_monkey.datastore.Account.query', new=mock_query)
    @patch('security_monkey.db.session.commit', new=mock_db_session.commit)
    def test_enable_all_accounts(self):
        from security_monkey.scheduler import enable_accounts
        enable_accounts(['TEST_ACCOUNT1', 'TEST_ACCOUNT2', 'TEST_ACCOUNT3', 'TEST_ACCOUNT4'])
        self.assertTrue(self.test_account1.active)
        self.assertTrue(self.test_account2.active)
        self.assertTrue(self.test_account3.active)
        self.assertTrue(self.test_account4.active)

    @patch('security_monkey.datastore.Account.query', new=mock_query)
    @patch('security_monkey.db.session.commit', new=mock_db_session.commit)
    def test_enable_one_accounts(self):
        from security_monkey.scheduler import enable_accounts
        enable_accounts(['TEST_ACCOUNT3'])
        self.assertTrue(self.test_account1.active)
        self.assertTrue(self.test_account2.active)
        self.assertTrue(self.test_account3.active)
        self.assertFalse(self.test_account4.active)

    @patch('security_monkey.datastore.Account.query', new=mock_query)
    @patch('security_monkey.db.session.commit', new=mock_db_session.commit)
    def test_enable_bad_accounts(self):
        from security_monkey.scheduler import enable_accounts
        enable_accounts(['BAD_ACCOUNT'])
        self.assertTrue(self.test_account1.active)
        self.assertTrue(self.test_account2.active)
        self.assertFalse(self.test_account3.active)
        self.assertFalse(self.test_account4.active)

    @patch('security_monkey.datastore.Account.query', new=mock_query)
    @patch('security_monkey.db.session.commit', new=mock_db_session.commit)
    def test_disable_bad_accounts(self):
        from security_monkey.scheduler import disable_accounts
        disable_accounts(['BAD_ACCOUNT'])
        self.assertTrue(self.test_account1.active)
        self.assertTrue(self.test_account2.active)
        self.assertFalse(self.test_account3.active)
        self.assertFalse(self.test_account4.active)
