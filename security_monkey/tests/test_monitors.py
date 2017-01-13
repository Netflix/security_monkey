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
from security_monkey.monitors import get_monitors_and_dependencies
from security_monkey.tests.db_mock import MockAccountQuery, MockDBSession
from security_monkey.datastore import Account, AccountType

from mock import patch
from collections import defaultdict

from security_monkey import app

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


class MockWatcher(object):
    def __init__(self, accounts=None, debug=False):
        self.accounts = accounts


class MockAuditor(object):
    support_auditor_indexes = []
    support_watcher_indexes = []

    def __init__(self, accounts=None, debug=False):
        self.accounts = accounts

    def applies_to_account(self, account):
        return True

test_watcher_registry = {}
test_auditor_registry = defaultdict(list)

watcher_configs = [
    { 'type': 'MockWatcher1', 'index': 'index1', 'account_type': 'AWS' },
    { 'type': 'MockWatcher2', 'index': 'index2', 'account_type': 'AWS' },
    { 'type': 'MockWatcher3', 'index': 'index3', 'account_type': 'AWS'  }
]

for config in watcher_configs:
    watcher = type(
                config['type'], (MockWatcher,),
                {
                    'index': config['index'],
                    'account_type': config['account_type']
                }
            )

    test_watcher_registry[config['index']] = watcher

auditor_configs = [
    {
        'type': 'MockAuditor1',
        'index': 'index1',
        'support_auditor_indexes': [],
        'support_watcher_indexes': ['index2']
    },
    {
        'type': 'MockAuditor2',
        'index': 'index2',
        'support_auditor_indexes': [],
        'support_watcher_indexes': []
    },
    {
        'type': 'MockAuditor3',
        'index': 'index3',
        'support_auditor_indexes': [],
        'support_watcher_indexes': ['index2']
    },
    {
        'type': 'MockAuditor4',
        'index': 'index3',
        'support_auditor_indexes': [],
        'support_watcher_indexes': []
    }
]

for config in auditor_configs:
    auditor = type(
                config['type'], (MockAuditor,),
                {
                    'index': config['index'],
                    'support_auditor_indexes': config['support_auditor_indexes'],
                    'support_watcher_indexes': config['support_watcher_indexes']
                }
            )

    test_auditor_registry[config['index']].append(auditor)

class MonitorTestCase(SecurityMonkeyTestCase):

    @patch('security_monkey.datastore.Account.query', new=mock_query)
    @patch('security_monkey.db.session.expunge', new=mock_db_session.expunge)
    @patch.dict(watcher_registry, test_watcher_registry, clear=True)
    @patch.dict(auditor_registry, test_auditor_registry, clear=True)
    def test_get_monitors_and_dependencies_all(self):
        mons = get_monitors_and_dependencies('TEST_ACCOUNT', test_watcher_registry.keys())
        assert len(mons) == 3

    @patch('security_monkey.datastore.Account.query', new=mock_query)
    @patch('security_monkey.db.session.expunge', new=mock_db_session.expunge)
    @patch.dict(watcher_registry, test_watcher_registry, clear=True)
    @patch.dict(auditor_registry, test_auditor_registry, clear=True)
    def test_get_monitors_and_dependencies_all_dependencies(self):
        mons = get_monitors_and_dependencies('TEST_ACCOUNT', ['index2'])
        assert len(mons) == 3

    @patch('security_monkey.datastore.Account.query', new=mock_query)
    @patch('security_monkey.db.session.expunge', new=mock_db_session.expunge)
    @patch.dict(watcher_registry, test_watcher_registry, clear=True)
    @patch.dict(auditor_registry, test_auditor_registry, clear=True)
    def test_get_monitors_and_dependencies_no_dependencies(self):
        mons = get_monitors_and_dependencies('TEST_ACCOUNT', ['index1'])
        assert len(mons) == 1
