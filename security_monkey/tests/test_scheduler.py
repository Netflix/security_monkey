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
from security_monkey.watcher import watcher_registry
from security_monkey.auditor import auditor_registry
from security_monkey.datastore import Account, AccountType
from security_monkey.tests.db_mock import MockAccountQuery, MockDBSession
from security_monkey.scheduler import find_changes

from mock import patch
from collections import defaultdict
from copy import copy

RUNTIME_WATCHERS = defaultdict(list)
RUNTIME_AUDITORS = defaultdict(list)

orig_watcher_registry = copy(watcher_registry)
orig_auditor_registry = copy(auditor_registry)


def slurp(self):
    RUNTIME_WATCHERS[self.__class__.__name__].append(self)
    item_list = []
    exception_map = {}
    return item_list, exception_map


def save(self):
    pass


def audit_all_objects(self):
    RUNTIME_AUDITORS[self.__class__.__name__].append(self)


def save_issues(self):
    pass


def applies_to_account(self, account):
    return True

mock_query = MockAccountQuery()
mock_db_session = MockDBSession()

test_account = Account()
test_account.name = "TEST_ACCOUNT"
test_account.notes = "TEST ACCOUNT"
test_account.s3_name = "TEST_ACCOUNT"
test_account.number = "012345678910"
test_account.role_name = "TEST_ACCOUNT"
test_account.account_type = AccountType(name='AWS')
test_account.third_party = False
test_account.active = True
mock_query.add_account(test_account)

test_account2 = Account()
test_account2.name = "TEST_ACCOUNT2"
test_account2.notes = "TEST ACCOUNT2"
test_account2.s3_name = "TEST_ACCOUNT2"
test_account2.number = "123123123123"
test_account2.role_name = "TEST_ACCOUNT"
test_account2.account_type = AccountType(name='AWS')
test_account2.third_party = False
test_account2.active = True
mock_query.add_account(test_account2)


class MockWatcher(object):

    def __init__(self, accounts=None, debug=False):
        self.accounts = accounts

    def find_changes(self, current=[], exception_map={}):
        pass


class MockAuditor(object):

    def __init__(self, accounts=None, debug=False):
        self.accounts = accounts

test_watcher_registry = {}
test_auditor_registry = {}
for key in watcher_registry:
    base_watcher_class = watcher_registry[key]
    test_watcher_registry[key] = type(
        base_watcher_class.__name__, (MockWatcher,),
        {
            'slurp': slurp,
            'save': save,
            'index': base_watcher_class.index,
            'account_type': base_watcher_class.account_type
        }
    )

for key in auditor_registry:
    auditor_list = []
    for base_auditor_class in auditor_registry[key]:
        auditor = type(
            base_auditor_class.__name__, (MockAuditor,),
            {
                'audit_all_objects': audit_all_objects,
                'save_issues': save_issues,
                'index': base_auditor_class.index,
                'support_auditor_indexes': base_auditor_class.support_auditor_indexes,
                'support_watcher_indexes': base_auditor_class.support_watcher_indexes,
                'applies_to_account': applies_to_account
            }
        )

        auditor_list.append(auditor)
    test_auditor_registry[key] = auditor_list


class SchedulerTestCase(SecurityMonkeyTestCase):

    @patch('security_monkey.datastore.Account.query', new=mock_query)
    @patch('security_monkey.db.session.expunge', new=mock_db_session.expunge)
    @patch.dict(watcher_registry, test_watcher_registry, clear=True)
    @patch.dict(auditor_registry, test_auditor_registry, clear=True)
    def test_find_all_changes(self):
        RUNTIME_AUDITORS.clear()
        RUNTIME_WATCHERS.clear()
        find_changes(['TEST_ACCOUNT', 'TEST_ACCOUNT2'],
                     watcher_registry.keys())

        expected_watcher_count = 0
        expected_auditor_count = 0
        for key in orig_watcher_registry:
            expected_watcher_count = expected_watcher_count + 1
            wa_list = RUNTIME_WATCHERS[orig_watcher_registry[key].__name__]
            self.assertEqual(first=len(wa_list), second=2,
                             msg="Watcher {} should run once but ran {} time(s)"
                             .format(orig_watcher_registry[key].__name__, len(wa_list)))

            for au in orig_auditor_registry[orig_watcher_registry[key].index]:
                expected_auditor_count = expected_auditor_count + 1
                au_list = RUNTIME_AUDITORS[au.__name__]
                self.assertEqual(first=len(au_list), second=2,
                                 msg="Auditor {} should run once but ran {} time(s)"
                                 .format(au.__name__, len(au_list)))

        self.assertEqual(first=len(RUNTIME_WATCHERS.keys()), second=expected_watcher_count,
                         msg="Should run {} watchers but ran {}"
                         .format(expected_watcher_count, len(RUNTIME_WATCHERS.keys())))

        self.assertEqual(first=len(RUNTIME_AUDITORS.keys()), second=expected_auditor_count,
                         msg="Should run {} auditor(s) but ran {}"
                         .format(expected_auditor_count, len(RUNTIME_AUDITORS.keys())))

    @patch('security_monkey.datastore.Account.query', new=mock_query)
    @patch('security_monkey.db.session.expunge', new=mock_db_session.expunge)
    @patch.dict(watcher_registry, test_watcher_registry, clear=True)
    @patch.dict(auditor_registry, test_auditor_registry, clear=True)
    def test_find_account_changes(self):
        RUNTIME_AUDITORS.clear()
        RUNTIME_WATCHERS.clear()
        find_changes(['TEST_ACCOUNT'], watcher_registry.keys())

        expected_watcher_count = 0
        expected_auditor_count = 0
        for key in orig_watcher_registry:
            expected_watcher_count = expected_watcher_count + 1
            wa_list = RUNTIME_WATCHERS[orig_watcher_registry[key].__name__]
            self.assertEqual(first=len(wa_list), second=1,
                             msg="Watcher {} should run once but ran {} time(s)"
                             .format(orig_watcher_registry[key].__name__, len(wa_list)))
            for au in auditor_registry[orig_watcher_registry[key].index]:
                expected_auditor_count = expected_auditor_count + 1
                au_list = RUNTIME_AUDITORS[au.__name__]
                self.assertEqual(first=len(au_list), second=1,
                                 msg="Auditor {} should run once but ran {} time(s)"
                                 .format(au.__name__, len(au_list)))

        self.assertEqual(first=len(RUNTIME_WATCHERS.keys()), second=expected_watcher_count,
                         msg="Should run {} watchers but ran {}"
                         .format(expected_watcher_count, len(RUNTIME_WATCHERS.keys())))

        self.assertEqual(first=len(RUNTIME_AUDITORS.keys()), second=expected_auditor_count,
                         msg="Should run {} auditor(s) but ran {}"
                         .format(expected_auditor_count, len(RUNTIME_AUDITORS.keys())))

    @patch('security_monkey.datastore.Account.query', new=mock_query)
    @patch('security_monkey.db.session.expunge', new=mock_db_session.expunge)
    @patch.dict(watcher_registry, test_watcher_registry, clear=True)
    @patch.dict(auditor_registry, test_auditor_registry, clear=True)
    def test_find_monitor_change(self):
        RUNTIME_AUDITORS.clear()
        RUNTIME_WATCHERS.clear()
        find_changes(['TEST_ACCOUNT'], ['s3'])

        self.assertEqual(first=len(RUNTIME_WATCHERS.keys()), second=1,
                         msg="Should run one watchers but ran {}"
                         .format(len(RUNTIME_WATCHERS.keys())))

        expected_auditor_count = 0
        for au in auditor_registry['s3']:
            expected_auditor_count = expected_auditor_count + 1
            au_list = RUNTIME_AUDITORS[au.__name__]
            self.assertEqual(first=len(au_list), second=1,
                             msg="Auditor {} should run once but ran {} time(s)"
                             .format(au.__name__, len(au_list)))

        self.assertEqual(first=len(RUNTIME_AUDITORS.keys()), second=expected_auditor_count,
                         msg="Should run {} auditor but ran {}"
                         .format(expected_auditor_count, len(RUNTIME_AUDITORS.keys())))
