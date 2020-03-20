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
.. module: security_monkey.tests.core.test_change_finder
    :platform: Unix

.. version:: $$VERSION$$
.. moduleauthor:: Bridgewater OSS <opensource@bwater.com>
"""

from mock import patch

from security_monkey import db, ARN_PREFIX
from security_monkey.datastore import Account, AccountType
from security_monkey.tests import SecurityMonkeyTestCase
from security_monkey.tests.core.monitor_mock import RUNTIME_WATCHERS, RUNTIME_AUDIT_COUNTS
from security_monkey.tests.core.monitor_mock import build_mock_result
from security_monkey.tests.core.monitor_mock import mock_get_monitors, mock_all_monitors
from security_monkey.watcher import ChangeItem

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

auditor_configs_with_watcher_dependencies = [
    {
        'index': 'index1',
        'support_auditor_indexes': [],
        'support_watcher_indexes': ['index2']
    },
    {
        'index': 'index2',
        'support_auditor_indexes': ['index1'],
        'support_watcher_indexes': []
    },
    {
        'index': 'index3',
        'support_auditor_indexes': [],
        'support_watcher_indexes': ['index1']
    }
]


class SomeTestItem(ChangeItem):
    def __init__(self, account=None, name=None, arn=None, config=None):
        super(SomeTestItem, self).__init__(
            index="iamrole",
            region='universal',
            account=account,
            name=name,
            arn=arn,
            new_config=config or {})

    @classmethod
    def from_slurp(cls, role, **kwargs):
        return cls(
            account=kwargs['account_name'],
            name=role['name'],
            config=role,
            arn=role['Arn'])


@patch('security_monkey.monitors.all_monitors', mock_all_monitors)
@patch('security_monkey.monitors.get_monitors', mock_get_monitors)
class ChangeFinderTestCase(SecurityMonkeyTestCase):
    test_account1 = None
    test_account2 = None
    test_account3 = None
    test_account4 = None

    def pre_test_setup(self):
        account_type_result = AccountType(name='AWS')
        db.session.add(account_type_result)
        db.session.commit()

        account = Account(identifier="012345678910", name="TEST_ACCOUNT1",
                          account_type_id=account_type_result.id, notes="TEST_ACCOUNT1",
                          third_party=False, active=True)
        db.session.add(account)

        account = Account(identifier="123123123123", name="TEST_ACCOUNT2",
                          account_type_id=account_type_result.id, notes="TEST_ACCOUNT2",
                          third_party=False, active=True)
        db.session.add(account)

        account = Account(identifier="109876543210", name="TEST_ACCOUNT3",
                          account_type_id=account_type_result.id, notes="TEST_ACCOUNT3",
                          third_party=False, active=False)
        db.session.add(account)

        account = Account(identifier="456456456456", name="TEST_ACCOUNT4",
                          account_type_id=account_type_result.id, notes="TEST_ACCOUNT4",
                          third_party=False, active=False)
        db.session.add(account)

        db.session.commit()

        RUNTIME_WATCHERS.clear()
        RUNTIME_AUDIT_COUNTS.clear()

    def test_find_all_changes(self):
        from security_monkey.task_scheduler.tasks import manual_run_change_finder, setup
        build_mock_result(watcher_configs, auditor_configs)
        setup()
        manual_run_change_finder(['TEST_ACCOUNT1', 'TEST_ACCOUNT2'], ['index1', 'index2', 'index3'])

        watcher_keys = list(RUNTIME_WATCHERS.keys())
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

        auditor_keys = list(RUNTIME_AUDIT_COUNTS.keys())
        self.assertEqual(first=3, second=len(auditor_keys),
                         msg="Should run 3 auditors but ran {}"
                         .format(len(auditor_keys)))

        self.assertTrue('index1' in auditor_keys,
                        msg="Auditor index1 not run")
        self.assertTrue('index2' in auditor_keys,
                        msg="Auditor index2 not run")
        self.assertTrue('index3' in auditor_keys,
                        msg="Auditor index3 not run")

        self.assertEqual(first=2, second=RUNTIME_AUDIT_COUNTS['index1'],
                         msg="Auditor index1 should have audited 2 items but audited {}"
                         .format(RUNTIME_AUDIT_COUNTS['index1']))
        self.assertEqual(first=2, second=RUNTIME_AUDIT_COUNTS['index2'],
                         msg="Auditor index2 should have audited 2 items but audited {}"
                         .format(RUNTIME_AUDIT_COUNTS['index2']))
        self.assertEqual(first=2, second=RUNTIME_AUDIT_COUNTS['index3'],
                         msg="Auditor index3 should have audited 2 items but audited {}"
                         .format(RUNTIME_AUDIT_COUNTS['index3']))

    def test_find_account_changes(self):
        from security_monkey.task_scheduler.tasks import manual_run_change_finder, setup
        build_mock_result(watcher_configs, auditor_configs)
        setup()
        manual_run_change_finder(['TEST_ACCOUNT1'], ['index1', 'index2', 'index3'])

        watcher_keys = list(RUNTIME_WATCHERS.keys())
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

        auditor_keys = list(RUNTIME_AUDIT_COUNTS.keys())
        self.assertEqual(first=3, second=len(auditor_keys),
                         msg="Should run 3 auditors but ran {}"
                         .format(len(auditor_keys)))

        self.assertTrue('index1' in auditor_keys,
                        msg="Auditor index1 not run")
        self.assertTrue('index2' in auditor_keys,
                        msg="Auditor index2 not run")
        self.assertTrue('index3' in auditor_keys,
                        msg="Auditor index3 not run")

        self.assertEqual(first=1, second=RUNTIME_AUDIT_COUNTS['index1'],
                         msg="Auditor index1 should have audited 1 item but audited {}"
                         .format(RUNTIME_AUDIT_COUNTS['index1']))
        self.assertEqual(first=1, second=RUNTIME_AUDIT_COUNTS['index2'],
                         msg="Auditor index2 should have audited 1 item but audited {}"
                         .format(RUNTIME_AUDIT_COUNTS['index2']))
        self.assertEqual(first=1, second=RUNTIME_AUDIT_COUNTS['index3'],
                         msg="Auditor index3 should have audited 1 item but audited {}"
                         .format(RUNTIME_AUDIT_COUNTS['index3']))
