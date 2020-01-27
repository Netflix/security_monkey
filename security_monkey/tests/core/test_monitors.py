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
.. module: security_monkey.tests.core.test_monitors
    :platform: Unix

.. version:: $$VERSION$$
.. moduleauthor:: Bridgewater OSS <opensource@bwater.com>


"""
from security_monkey.tests import SecurityMonkeyTestCase
from security_monkey.watcher import watcher_registry
from security_monkey.auditor import auditor_registry
from security_monkey.monitors import get_monitors_and_dependencies
from security_monkey.datastore import Account, AccountType
from security_monkey import db
from security_monkey.watcher import Watcher
from security_monkey.auditor import Auditor

from mock import patch
from collections import defaultdict


class MockWatcher(Watcher):
    def __init__(self, accounts=None, debug=False):
        super(MockWatcher, self).__init__(accounts=accounts, debug=debug)


class MockAuditor(Auditor):
    def __init__(self, accounts=None, debug=False):
        super(MockAuditor, self).__init__(accounts=accounts, debug=debug)


test_watcher_registry = {}
test_auditor_registry = defaultdict(list)

watcher_configs = [
    {'type': 'MockWatcher1', 'index': 'index1'},
    {'type': 'MockWatcher2', 'index': 'index2'},
    {'type': 'MockWatcher3', 'index': 'index3'}
]

for config in watcher_configs:
    watcher = type(config['type'], (MockWatcher,), {'index': config['index']})
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
    def pre_test_setup(self):
        account_result = Account.query.filter(Account.name == 'TEST_ACCOUNT').first()
        if not account_result:
            account_type = AccountType(name='AWS')
            db.session.add(account_type)
            db.session.commit()

            account_result = Account(
                name='TEST_ACCOUNT',
                identifier='012345678910',
                third_party=False, active=True,
                account_type_id=account_type.id
            )
            db.session.add(account_result)
            db.session.commit()

    def tearDown(self):
        import security_monkey.auditor
        security_monkey.auditor.auditor_registry = defaultdict(list)
        super(MonitorTestCase, self).tearDown()

    @patch.dict(watcher_registry, test_watcher_registry, clear=True)
    @patch.dict(auditor_registry, test_auditor_registry, clear=True)
    def test_get_monitors_and_dependencies_all(self):
        mons = get_monitors_and_dependencies('TEST_ACCOUNT', list(test_watcher_registry.keys()))
        assert len(mons) == 3

    @patch.dict(watcher_registry, test_watcher_registry, clear=True)
    @patch.dict(auditor_registry, test_auditor_registry, clear=True)
    def test_get_monitors_and_dependencies_all_dependencies(self):
        mons = get_monitors_and_dependencies('TEST_ACCOUNT', ['index2'])
        assert len(mons) == 3

    @patch.dict(watcher_registry, test_watcher_registry, clear=True)
    @patch.dict(auditor_registry, test_auditor_registry, clear=True)
    def test_get_monitors_and_dependencies_no_dependencies(self):
        mons = get_monitors_and_dependencies('TEST_ACCOUNT', ['index1'])
        assert len(mons) == 1
