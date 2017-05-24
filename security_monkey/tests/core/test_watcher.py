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
.. module: security_monkey.tests.core.test_watcher
    :platform: Unix

.. version:: $$VERSION$$
.. moduleauthor:: Bridgewater OSS <opensource@bwater.com>


"""
import datetime
import json

from security_monkey.watcher import Watcher, ChangeItem
from security_monkey.datastore import Account, AccountType, Datastore, Item, ItemAudit, Technology, ItemRevision
from security_monkey import db

from security_monkey.tests import SecurityMonkeyTestCase


CONFIG_1 = {
    'key1': 'value1',
    'key2': 'value2',
    'key3': 'value3',
    'key4': 'value4'
}

CONFIG_2 = {
    'key1': 'value1',
    'key2': 'value2',
    'key3': 'value3',
    'key4': 'newvalue'
}

ACTIVE_CONF = {
    "account_number": "012345678910",
    "technology": "iamrole",
    "region": "universal",
    "name": "SomeRole",
    "policy": {
        "Statement": [
            {
                "Effect": "Deny",
                "Action": "*",
                "Resource": "*"
            }
        ]
    },
    "Arn": "arn:aws:iam::012345678910:role/SomeRole"
}

ASPD = {
    "Arn": "arn:aws:iam::012345678910:role/SomeRole",
    "Path": "/",
    "RoleId": "a2wdg1234x12ih4maj4mv",
    "RoleName": "SomeRole",
    "CreateDate": datetime.datetime.utcnow(),
    "AssumeRolePolicyDocument": {
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


class WatcherTestCase(SecurityMonkeyTestCase):
    def test_from_items(self):
        issue = ItemAudit()
        issue.score = 1
        issue.justified = True
        issue.issue = 'test issue'
        issue.justification = 'test justification'

        old_item_w_issues = ChangeItem(index='testtech', region='us-west-2', account='testaccount',
                                      new_config=CONFIG_1, active=True, audit_issues=[issue])
        old_item_wo_issues = ChangeItem(index='testtech', region='us-west-2', account='testaccount',
                                        new_config=CONFIG_1, active=True)
        new_item = ChangeItem(index='testtech', region='us-west-2', account='testaccount', new_config=CONFIG_2,
                              active=True)

        merged_item_w_issues = ChangeItem.from_items(old_item=old_item_w_issues, new_item=new_item)
        merged_item_wo_issues = ChangeItem.from_items(old_item=old_item_wo_issues, new_item=new_item)

        assert len(merged_item_w_issues.audit_issues) == 1
        assert len(merged_item_wo_issues.audit_issues) == 0

    def setup_batch_db(self):
        account_type_result = AccountType(name='AWS')
        db.session.add(account_type_result)
        db.session.commit()

        self.account = Account(identifier="012345678910", name="testing",
                               active=True, third_party=False,
                               account_type_id=account_type_result.id)
        self.technology = Technology(name="iamrole")

        db.session.add(self.account)
        db.session.add(self.technology)
        db.session.commit()

    def test_no_change_items(self):
        previous = [
            ChangeItem(
                index='test_index',
                account='test_account',
                name='item1_name',
                new_config={
                    'config': 'test1'
                }
            ),
            ChangeItem(
                index='test_index',
                account='test_account',
                name='item2_name',
                new_config={
                    'config': 'test2'
                }
            )
        ]

        current = [
            ChangeItem(
                index='test_index',
                account='test_account',
                name='item1_name',
                new_config={
                    'config': 'test1'
                }
            ),
            ChangeItem(
                index='test_index',
                account='test_account',
                name='item2_name',
                new_config={
                    'config': 'test2'
                }
            )
        ]

        self._setup_account()
        watcher = Watcher(accounts=['test_account'])

        watcher.find_modified(previous, current)
        assert len(watcher.changed_items) == 0

    def test_changed_item(self):

        previous = [
            ChangeItem(
                index='test_index',
                account='test_account',
                name='item1_name',
                new_config={
                    'config': 'test1'
                }
            ),
            ChangeItem(
                index='test_index',
                account='test_account',
                name='item2_name',
                new_config={
                    'config': 'test2'
                }
            )
        ]

        current = [
            ChangeItem(
                index='test_index',
                account='test_account',
                name='item1_name',
                new_config={
                    'config': 'test1'
                }
            ),
            ChangeItem(
                index='test_index',
                account='test_account',
                name='item2_name',
                new_config={
                    'config': 'test3'
                }
            )
        ]

        self._setup_account()
        watcher = Watcher(accounts=['test_account'])

        watcher.find_modified(previous, current)
        assert len(watcher.changed_items) == 1

    def test_ephemeral_change(self):

        previous = [
            ChangeItem(
                index='test_index',
                account='test_account',
                name='item1_name',
                new_config={
                    'normal': True
                }
            ),
            ChangeItem(
                index='test_index',
                account='test_account',
                name='item2_name',
                new_config={
                    'normal': False,
                    'test_ephemeral': 'previous ephemeral'
                }
            )
        ]

        current = [
            ChangeItem(
                index='test_index',
                account='test_account',
                name='item1_name',
                new_config={
                    'normal': True
                }
            ),
            ChangeItem(
                index='test_index',
                account='test_account',
                name='item2_name',
                new_config={
                    'normal': False,
                    'test_ephemeral': 'current ephemeral'
                }
            )
        ]

        self._setup_account()
        watcher = Watcher(accounts=['test_account'])
        watcher.honor_ephemerals = True
        watcher.ephemeral_paths = ['test_ephemeral']

        watcher.find_modified(previous, current)
        assert len(watcher.changed_items) == 0

    def test_save_changed_item(self):
        self._setup_account()

        datastore = Datastore()

        old_item = ChangeItem(
                index='test_index',
                account='test_account',
                name='item_name',
                active=True,
                new_config={
                    'config': 'test1'
                }
            )

        old_item.save(datastore)

        query = Item.query.filter(Technology.name == 'test_index').filter(Account.name == 'test_account')
        items = query.all()
        self.assertEquals(len(items), 1)
        revisions = items[0].revisions.all()
        self.assertEquals(len(revisions), 1)

        new_item = ChangeItem(
                index='test_index',
                account='test_account',
                name='item_name',
                active=True,
                new_config={
                    'config': 'test2'
                }
            )
        watcher = Watcher(accounts=['test_account'])
        watcher.index = 'test_index'
        watcher.find_changes(current=[new_item])
        watcher.save()

        query = Item.query.filter(Technology.name == 'test_index').filter(Account.name == 'test_account')
        items = query.all()
        self.assertEquals(len(items), 1)
        revisions = items[0].revisions.all()
        self.assertEquals(len(revisions), 2)

    def test_save_ephemeral_changed_item(self):
        self._setup_account()

        datastore = Datastore()

        old_item = ChangeItem(
                index='test_index',
                account='test_account',
                name='item_name',
                active=True,
                new_config={
                    'config': 'test1'
                }
            )

        old_item.save(datastore)

        query = Item.query.filter(Technology.name == 'test_index').filter(Account.name == 'test_account')
        items = query.all()
        self.assertEquals(len(items), 1)
        revisions = items[0].revisions.all()
        self.assertEquals(len(revisions), 1)

        new_item = ChangeItem(
                index='test_index',
                account='test_account',
                name='item_name',
                active=True,
                new_config={
                    'config': 'test2'
                }
            )
        watcher = Watcher(accounts=['test_account'])
        watcher.index = 'test_index'
        watcher.honor_ephemerals = True
        watcher.ephemeral_paths = ["config"]

        watcher.find_changes(current=[new_item])
        watcher.save()

        query = Item.query.filter(Technology.name == 'test_index').filter(Account.name == 'test_account')
        items = query.all()
        self.assertEquals(len(items), 1)
        revisions = items[0].revisions.all()
        self.assertEquals(len(revisions), 1)

    def _setup_account(self):
        account_type_result = AccountType(name='AWS')
        db.session.add(account_type_result)
        db.session.commit()

        account = Account(identifier="012345678910", name="test_account",
                          third_party=False, active=True,
                          account_type_id=account_type_result.id)

        db.session.add(account)
        db.session.commit()

    def test_find_changes_batch(self):
        """
        This will test the entry point via the find_changes() method vs. the find_changes_batch() method.

        This will also use the IAMRole watcher, since that already has batching support.
        :return:
        """
        from security_monkey.watchers.iam.iam_role import IAMRole

        self.setup_batch_db()

        watcher = IAMRole(accounts=[self.account.name])
        watcher.current_account = (self.account, 0)
        watcher.technology = self.technology

        items = []
        for x in range(0, 5):
            mod_conf = dict(ACTIVE_CONF)
            mod_conf["name"] = "SomeRole{}".format(x)
            mod_conf["Arn"] = "arn:aws:iam::012345678910:role/SomeRole{}".format(x)

            items.append(SomeTestItem().from_slurp(mod_conf, account_name=self.account.name))

        assert len(watcher.find_changes(items)) == 5
        assert len(watcher.deleted_items) == 0
        assert len(watcher.changed_items) == 0
        assert len(watcher.created_items) == 5

        watcher_2 = IAMRole(accounts=[self.account.name])
        watcher_2.current_account = (self.account, 0)
        watcher_2.technology = self.technology

        # Try again -- audit_items should be 0 since nothing was changed:
        assert len(watcher_2.find_changes(items)) == 0
        assert len(watcher_2.deleted_items) == 0
        assert len(watcher_2.changed_items) == 0
        assert len(watcher_2.created_items) == 0

    def test_find_deleted_batch(self):
        """
        This will use the IAMRole watcher, since that already has batching support.
        :return:
        """
        from security_monkey.watchers.iam.iam_role import IAMRole

        self.setup_batch_db()

        # Set everything up:
        watcher = IAMRole(accounts=[self.account.name])
        watcher.current_account = (self.account, 0)
        watcher.technology = self.technology

        items = []
        for x in range(0, 5):
            mod_conf = dict(ACTIVE_CONF)
            mod_conf["name"] = "SomeRole{}".format(x)
            mod_conf["Arn"] = "arn:aws:iam::012345678910:role/SomeRole{}".format(x)
            items.append(SomeTestItem().from_slurp(mod_conf, account_name=self.account.name))

            mod_aspd = dict(ASPD)
            mod_aspd["Arn"] = "arn:aws:iam::012345678910:role/SomeRole{}".format(x)
            mod_aspd["RoleName"] = "SomeRole{}".format(x)
            watcher.total_list.append(mod_aspd)

        watcher.find_changes(items)

        # Check for deleted items:
        watcher.find_deleted_batch({})
        assert len(watcher.deleted_items) == 0

        # Check that nothing was deleted:
        for x in range(0, 5):
            item_revision = ItemRevision.query.join((Item, ItemRevision.id == Item.latest_revision_id)).filter(
                Item.arn == "arn:aws:iam::012345678910:role/SomeRole{}".format(x),
            ).one()

            assert item_revision.active

            # Create some issues for testing purposes:
            db.session.add(ItemAudit(score=10,
                                     issue="IAM Role has full admin permissions.",
                                     notes=json.dumps(item_revision.config),
                                     item_id=item_revision.item_id))
            db.session.add(ItemAudit(score=9001, issue="Some test issue", notes="{}", item_id=item_revision.item_id))

        db.session.commit()
        assert len(ItemAudit.query.all()) == len(items) * 2

        # Remove the last two items:
        removed_arns = []
        removed_arns.append(watcher.total_list.pop()["Arn"])
        removed_arns.append(watcher.total_list.pop()["Arn"])

        # Check for deleted items again:
        watcher.find_deleted_batch({})
        assert len(watcher.deleted_items) == 2

        # Check that the last two items were deleted:
        for arn in removed_arns:
            item_revision = ItemRevision.query.join((Item, ItemRevision.id == Item.latest_revision_id)).filter(
                Item.arn == arn,
            ).one()

            assert not item_revision.active

        # Check that the current ones weren't deleted:
        for current_item in watcher.total_list:
            item_revision = ItemRevision.query.join((Item, ItemRevision.id == Item.latest_revision_id)).filter(
                Item.arn == current_item["Arn"],
            ).one()

            assert item_revision.active
            assert len(ItemAudit.query.filter(ItemAudit.item_id == item_revision.item_id).all()) == 2
