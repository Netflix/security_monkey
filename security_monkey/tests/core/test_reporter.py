#     Copyright 2017 Bridgewater Associates
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
.. module: security_monkey.tests.test_reporter
    :platform: Unix

.. version:: $$VERSION$$
.. moduleauthor:: Bridgewater OSS <opensource@bwater.com>

"""
import json

import boto3
from moto import mock_iam
from moto import mock_sts

from security_monkey.tests import SecurityMonkeyTestCase
from security_monkey.datastore import Account, AccountType
from security_monkey.tests.core.monitor_mock import RUNTIME_WATCHERS, RUNTIME_AUDIT_COUNTS
from security_monkey.tests.core.monitor_mock import build_mock_result
from security_monkey.tests.core.monitor_mock import mock_all_monitors
from security_monkey import db

from mock import patch

watcher_configs = [
    {'index': 'index1', 'interval': 15},
    {'index': 'index2', 'interval': 15},
    {'index': 'index3', 'interval': 60}
]

auditor_configs_no_external_dependencies = [
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
        'support_watcher_indexes': []
    }
]

auditor_configs_with_auditor_dependencies = [
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
        'support_auditor_indexes': ['index1'],
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

OPEN_POLICY = {
    "Statement": [
        {
            "Effect": "Allow",
            "Action": "*",
            "Resource": "*"
        }
    ]
}


def mock_report(self):
    pass


@patch('security_monkey.monitors.all_monitors', mock_all_monitors)
class ReporterTestCase(SecurityMonkeyTestCase):
    def pre_test_setup(self):
        account_type_result = AccountType(name='AWS')
        db.session.add(account_type_result)
        db.session.commit()

        account = Account(identifier="012345678910", name="TEST_ACCOUNT",
                          account_type_id=account_type_result.id, notes="TEST_ACCOUNT",
                          third_party=False, active=True)

        db.session.add(account)
        db.session.commit()

        RUNTIME_WATCHERS.clear()
        RUNTIME_AUDIT_COUNTS.clear()

    @patch('security_monkey.alerter.Alerter.report', new=mock_report)
    def test_run_with_interval_no_dependencies(self):
        """
        If an interval is passed to reporter.run(), the reporter will run all watchers in the interval
        along with their auditors. It will also reaudit all existing items of watchers that are not in
        the interval but are dependent on watchers/auditors in the interval. This is done because any
        changes to the dependencies could change the audit results even is the items have not changed.

        In this case, index1 and index2 are in the interval and index3 is not dependent on either.
        Expected result:
        Watchers of index1 and index2 are run
        New items of index1 and index2 are audited
        Items of index3 are not reaudited
        """
        from security_monkey.reporter import Reporter
        build_mock_result(watcher_configs, auditor_configs_no_external_dependencies)

        reporter = Reporter(account="TEST_ACCOUNT")
        reporter.run("TEST_ACCOUNT", 15)
        watcher_keys = RUNTIME_WATCHERS.keys()
        self.assertEqual(first=2, second=len(watcher_keys),
                         msg="Should run 2 watchers but ran {}"
                         .format(len(watcher_keys)))

        self.assertTrue('index1' in watcher_keys,
                        msg="Watcher index1 not run")
        self.assertTrue('index2' in watcher_keys,
                        msg="Watcher index2 not run")

        self.assertEqual(first=1, second=len(RUNTIME_WATCHERS['index1']),
                         msg="Watcher index1 should run once but ran {} times"
                         .format(len(RUNTIME_WATCHERS['index1'])))
        self.assertEqual(first=1, second=len(RUNTIME_WATCHERS['index2']),
                         msg="Watcher index2 should run once but ran {} times"
                         .format(len(RUNTIME_WATCHERS['index2'])))

        auditor_keys = RUNTIME_AUDIT_COUNTS.keys()
        self.assertEqual(first=3, second=len(auditor_keys),
                         msg="Should run all 3 auditors but ran {}"
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
        self.assertEqual(first=0, second=RUNTIME_AUDIT_COUNTS['index3'],
                         msg="Auditor index3 should have audited no items but audited {}"
                         .format(RUNTIME_AUDIT_COUNTS['index3']))

    @patch('security_monkey.alerter.Alerter.report', new=mock_report)
    def test_run_with_interval_auditor_dependencies(self):
        """
        If an interval is passed to reporter.run(), the reporter will run all watchers in the interval
        along with their auditors. It will also reaudit all existing items of watchers that are not in
        the interval but are dependent on watchers/auditors in the interval. This is done because any
        changes to the dependencies could change the audit results even is the items have not changed.

        In this case, index1 and index2 are in the interval and index3 is dependent on index1 auditor.
        Expected result:
        Watchers of index1 and index2 are run
        New items of index1 and index2 are audited
        Items of index3 are reaudited
        """
        from security_monkey.reporter import Reporter
        build_mock_result(watcher_configs, auditor_configs_with_auditor_dependencies)

        reporter = Reporter(account="TEST_ACCOUNT")
        reporter.run("TEST_ACCOUNT", 15)
        watcher_keys = RUNTIME_WATCHERS.keys()
        self.assertEqual(first=2, second=len(watcher_keys),
                         msg="Should run 2 watchers but ran {}"
                         .format(len(watcher_keys)))

        self.assertTrue('index1' in watcher_keys,
                        msg="Watcher index1 not run")
        self.assertTrue('index2' in watcher_keys,
                        msg="Watcher index2 not run")

        self.assertEqual(first=1, second=len(RUNTIME_WATCHERS['index1']),
                         msg="Watcher index1 should run once but ran {} times"
                         .format(len(RUNTIME_WATCHERS['index1'])))
        self.assertEqual(first=1, second=len(RUNTIME_WATCHERS['index2']),
                         msg="Watcher index2 should run once but ran {} times"
                         .format(len(RUNTIME_WATCHERS['index2'])))

        auditor_keys = RUNTIME_AUDIT_COUNTS.keys()
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

    @patch('security_monkey.alerter.Alerter.report', new=mock_report)
    def test_run_with_interval_watcher_dependencies(self):
        """
        If an interval is passed to reporter.run(), the reporter will run all watchers in the interval
        along with their auditors. It will also reaudit all existing items of watchers that are not in
        the interval but are dependent on watchers/auditors in the interval. This is done because any
        changes to the dependencies could change the audit results even is the items have not changed.

        In this case, index1 and index2 are in the interval and index3 is dependent on index1 watcher.
        Expected result:
        Watchers of index1 and index2 are run
        New items of index1 and index2 are audited
        Items of index3 are reaudited
        """
        from security_monkey.reporter import Reporter
        build_mock_result(watcher_configs, auditor_configs_with_watcher_dependencies)

        reporter = Reporter(account="TEST_ACCOUNT")
        reporter.run("TEST_ACCOUNT", 15)
        watcher_keys = RUNTIME_WATCHERS.keys()
        self.assertEqual(first=2, second=len(watcher_keys),
                         msg="Should run 2 watchers but ran {}"
                         .format(len(watcher_keys)))

        self.assertTrue('index1' in watcher_keys,
                        msg="Watcher index1 not run")
        self.assertTrue('index2' in watcher_keys,
                        msg="Watcher index2 not run")

        self.assertEqual(first=1, second=len(RUNTIME_WATCHERS['index1']),
                         msg="Watcher index1 should have audited 1 item but audited {}"
                         .format(len(RUNTIME_WATCHERS['index1'])))
        self.assertEqual(first=1, second=len(RUNTIME_WATCHERS['index2']),
                         msg="Watcher index2 should have audited 1 item but audited {}"
                         .format(len(RUNTIME_WATCHERS['index2'])))

        auditor_keys = RUNTIME_AUDIT_COUNTS.keys()
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
                         msg="Auditor index1 should run once but ran {} times"
                         .format(RUNTIME_AUDIT_COUNTS['index1']))
        self.assertEqual(first=1, second=RUNTIME_AUDIT_COUNTS['index2'],
                         msg="Auditor index2 should run once but ran {} times"
                         .format(RUNTIME_AUDIT_COUNTS['index2']))
        self.assertEqual(first=1, second=RUNTIME_AUDIT_COUNTS['index3'],
                         msg="Auditor index3 should run once but ran {} times"
                         .format(RUNTIME_AUDIT_COUNTS['index3']))

    def add_roles(self, initial=True):
        mock_iam().start()
        mock_sts().start()

        mock_iam().start()
        client = boto3.client("iam")

        aspd = {
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": "sts:AssumeRole",
                    "Principal": {
                        "Service": "ec2.amazonaws.com"
                    }
                }
            ]
        }

        if initial:
            last = 11
        else:
            last = 9  # Simulates 2 deleted roles...

        for x in range(0, last):
            # Create the IAM Role via Moto:
            aspd["Statement"][0]["Resource"] = "arn:aws:iam:012345678910:role/roleNumber{}".format(x)
            client.create_role(Path="/", RoleName="roleNumber{}".format(x),
                               AssumeRolePolicyDocument=json.dumps(aspd, indent=4))
            client.put_role_policy(RoleName="roleNumber{}".format(x), PolicyName="testpolicy",
                                   PolicyDocument=json.dumps(OPEN_POLICY, indent=4))


    def test_report_batch_changes(self):
        from security_monkey.alerter import Alerter
        from security_monkey.reporter import Reporter
        from security_monkey.datastore import Item, ItemRevision, ItemAudit
        from security_monkey.monitors import Monitor
        from security_monkey.watchers.iam.iam_role import IAMRole
        from security_monkey.auditors.iam.iam_role import IAMRoleAuditor

        account_type_result = AccountType.query.filter(AccountType.name == "AWS").one()
        db.session.add(account_type_result)
        db.session.commit()

        test_account = Account(identifier="012345678910", name="TEST_ACCOUNT",
                          account_type_id=account_type_result.id, notes="TEST_ACCOUNT1",
                          third_party=False, active=True)
        watcher = IAMRole(accounts=[test_account.name])
        db.session.commit()

        watcher.batched_size = 3  # should loop 4 times

        self.add_roles()

        # Set up the monitor:
        batched_monitor = Monitor(IAMRole, test_account)
        batched_monitor.watcher = watcher
        batched_monitor.auditors = [IAMRoleAuditor(accounts=[test_account.name])]

        # Set up the Reporter:
        import security_monkey.reporter
        old_all_monitors = security_monkey.reporter.all_monitors
        security_monkey.reporter.all_monitors = lambda x, y: []

        test_reporter = Reporter()
        test_reporter.all_monitors = [batched_monitor]
        test_reporter.account_alerter = Alerter(watchers_auditors=test_reporter.all_monitors, account=test_account.name)

        import security_monkey.scheduler
        # import security_monkey.monitors
        # old_get_monitors = security_monkey.scheduler.get_monitors
        security_monkey.scheduler.get_monitors = lambda x, y, z: [batched_monitor]

        # Moto screws up the IAM Role ARN -- so we need to fix it:
        original_slurp_list = watcher.slurp_list
        original_slurp = watcher.slurp

        def mock_slurp_list():
            items, exception_map = original_slurp_list()

            for item in watcher.total_list:
                item["Arn"] = "arn:aws:iam::012345678910:role/{}".format(item["RoleName"])

            return items, exception_map

        def mock_slurp():
            batched_items, exception_map = original_slurp()

            for item in batched_items:
                item.arn = "arn:aws:iam::012345678910:role/{}".format(item.name)
                item.config["Arn"] = item.arn
                item.config["RoleId"] = item.name  # Need this to stay the same

            return batched_items, exception_map

        watcher.slurp_list = mock_slurp_list
        watcher.slurp = mock_slurp

        test_reporter.run(account=test_account.name)

        # Check that all items were added to the DB:
        assert len(Item.query.all()) == 11

        # Check that we have exactly 11 item revisions:
        assert len(ItemRevision.query.all()) == 11

        # Check that there are audit issues for all 11 items:
        assert len(ItemAudit.query.all()) == 11

        mock_iam().stop()
        mock_sts().stop()

        # Something isn't cleaning itself up properly and causing other core tests to fail.
        # This is the solution:
        security_monkey.reporter.all_monitors = old_all_monitors
        import monitor_mock
        security_monkey.scheduler.get_monitors = monitor_mock.mock_get_monitors
