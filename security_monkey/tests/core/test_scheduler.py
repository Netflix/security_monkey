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
.. module: security_monkey.tests.core.test_scheduler
    :platform: Unix

.. version:: $$VERSION$$
.. moduleauthor:: Bridgewater OSS <opensource@bwater.com>

"""
import json

import boto3
from moto import mock_iam
from moto import mock_sts

from security_monkey.tests import SecurityMonkeyTestCase
from security_monkey.datastore import Account, AccountType, Technology, Item, ItemAudit, ItemRevision
from security_monkey.tests.core.monitor_mock import RUNTIME_WATCHERS, RUNTIME_AUDIT_COUNTS
from security_monkey.tests.core.monitor_mock import build_mock_result
from security_monkey.tests.core.monitor_mock import mock_get_monitors, mock_all_monitors
from security_monkey import db

from mock import patch

from security_monkey.watcher import ChangeItem, Watcher

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

OPEN_POLICY = {
    "Statement": [
        {
            "Effect": "Allow",
            "Action": "*",
            "Resource": "*"
        }
    ]
}

ROLE_CONF = {
    "account_number": "012345678910",
    "technology": "iamrole",
    "region": "universal",
    "name": "roleNumber",
    "InlinePolicies": {"ThePolicy": OPEN_POLICY},
    "Arn": "arn:aws:iam::012345678910:role/roleNumber"
}


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
class SchedulerTestCase(SecurityMonkeyTestCase):
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

    def test_find_batch_changes(self):
        """
        Runs through a full find job via the IAMRole watcher, as that supports batching.

        However, this is mostly testing the logic through each function call -- this is
        not going to do any boto work and that will instead be mocked out.
        :return:
        """
        from security_monkey.scheduler import find_changes
        from security_monkey.monitors import Monitor
        from security_monkey.watchers.iam.iam_role import IAMRole
        from security_monkey.auditors.iam.iam_role import IAMRoleAuditor

        test_account = Account(name="TEST_ACCOUNT1")
        watcher = IAMRole(accounts=[test_account.name])

        technology = Technology(name="iamrole")
        db.session.add(technology)
        db.session.commit()

        watcher.batched_size = 3  # should loop 4 times

        self.add_roles()

        # Set up the monitor:
        batched_monitor = Monitor(IAMRole, test_account)
        batched_monitor.watcher = watcher
        batched_monitor.auditors = [IAMRoleAuditor(accounts=[test_account.name])]

        import security_monkey.scheduler
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

        find_changes([test_account.name], test_account.name)

        # Check that all items were added to the DB:
        assert len(Item.query.all()) == 11

        # Check that we have exactly 11 item revisions:
        assert len(ItemRevision.query.all()) == 11

        # Check that there are audit issues for all 11 items:
        assert len(ItemAudit.query.all()) == 11

        # Delete one of the items:
        # Moto lacks implementation for "delete_role" (and I'm too lazy to submit a PR :D) -- so need to create again...
        mock_iam().stop()
        mock_sts().stop()
        self.add_roles(initial=False)

        # Run the it again:
        watcher.current_account = None  # Need to reset the watcher
        find_changes([test_account.name], test_account.name)

        # Check that nothing new was added:
        assert len(Item.query.all()) == 11

        # There should be the same number of issues and 2 more revisions:
        assert len(ItemAudit.query.all()) == 11 
        assert len(ItemRevision.query.all()) == 13

        # Check that the deleted roles show as being inactive:
        ir = ItemRevision.query.join((Item, ItemRevision.id == Item.latest_revision_id)) \
            .filter(Item.arn.in_(
                ["arn:aws:iam::012345678910:role/roleNumber9",
                 "arn:aws:iam::012345678910:role/roleNumber10"])).all()

        assert len(ir) == 2
        assert not ir[0].active
        assert not ir[1].active

        # Finally -- test with a slurp list exception (just checking that things don't blow up):
        def mock_slurp_list_with_exception():
            import security_monkey.watchers.iam.iam_role
            security_monkey.watchers.iam.iam_role.list_roles = lambda **kwargs: 1 / 0

            items, exception_map = original_slurp_list()

            assert len(exception_map) > 0
            return items, exception_map

        watcher.slurp_list = mock_slurp_list_with_exception
        watcher.current_account = None  # Need to reset the watcher
        find_changes([test_account.name], test_account.name)

        mock_iam().stop()
        mock_sts().stop()

    def test_audit_specific_changes(self):
        from security_monkey.scheduler import _audit_specific_changes
        from security_monkey.monitors import Monitor
        from security_monkey.watchers.iam.iam_role import IAMRole
        from security_monkey.cloudaux_watcher import CloudAuxChangeItem
        from security_monkey.auditors.iam.iam_role import IAMRoleAuditor

        # Set up the monitor:
        test_account = Account.query.filter(Account.name == "TEST_ACCOUNT1").one()
        batched_monitor = Monitor(IAMRole, test_account)
        batched_monitor.auditors = [IAMRoleAuditor(accounts=[test_account.name])]

        technology = Technology(name="iamrole")
        db.session.add(technology)
        db.session.commit()

        watcher = Watcher(accounts=[test_account.name])
        watcher.current_account = (test_account, 0)
        watcher.technology = technology

        # Create some IAM roles for testing:
        items = []
        for x in range(0, 3):
            role_policy = dict(ROLE_CONF)
            role_policy["Arn"] = "arn:aws:iam::012345678910:role/roleNumber{}".format(x)
            role_policy["RoleName"] = "roleNumber{}".format(x)
            role = CloudAuxChangeItem.from_item(name=role_policy['RoleName'], item=role_policy, override_region='universal', account_name=test_account.name, index='iamrole')
            items.append(role)

        audit_items = watcher.find_changes_batch(items, {})
        assert len(audit_items) == 3

        # Perform the audit:
        _audit_specific_changes(batched_monitor, audit_items, False)

        # Check all the issues are there:
        assert len(ItemAudit.query.all()) == 3

    def test_disable_all_accounts(self):
        from security_monkey.scheduler import disable_accounts
        disable_accounts(['TEST_ACCOUNT1', 'TEST_ACCOUNT2', 'TEST_ACCOUNT3', 'TEST_ACCOUNT4'])
        accounts = Account.query.all()
        for account in accounts:
            self.assertFalse(account.active)

    def test_disable_one_accounts(self):
        from security_monkey.scheduler import disable_accounts
        disable_accounts(['TEST_ACCOUNT1'])
        accounts = Account.query.all()
        for account in accounts:
            if account.name == 'TEST_ACCOUNT2':
                self.assertTrue(account.active)
            else:
                self.assertFalse(account.active)

    def test_enable_all_accounts(self):
        from security_monkey.scheduler import enable_accounts
        enable_accounts(['TEST_ACCOUNT1', 'TEST_ACCOUNT2', 'TEST_ACCOUNT3', 'TEST_ACCOUNT4'])
        accounts = Account.query.all()
        for account in accounts:
            self.assertTrue(account.active)

    def test_enable_one_accounts(self):
        from security_monkey.scheduler import enable_accounts
        enable_accounts(['TEST_ACCOUNT3'])
        accounts = Account.query.all()
        for account in accounts:
            if account.name != 'TEST_ACCOUNT4':
                self.assertTrue(account.active)
            else:
                self.assertFalse(account.active)

    def test_enable_bad_accounts(self):
        from security_monkey.scheduler import enable_accounts
        enable_accounts(['BAD_ACCOUNT'])
        accounts = Account.query.all()
        for account in accounts:
            if account.name == 'TEST_ACCOUNT1' or account.name == 'TEST_ACCOUNT2':
                self.assertTrue(account.active)
            else:
                self.assertFalse(account.active)

    def test_disable_bad_accounts(self):
        from security_monkey.scheduler import disable_accounts
        disable_accounts(['BAD_ACCOUNT'])
        accounts = Account.query.all()
        for account in accounts:
            if account.name == 'TEST_ACCOUNT1' or account.name == 'TEST_ACCOUNT2':
                self.assertTrue(account.active)
            else:
                self.assertFalse(account.active)

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
