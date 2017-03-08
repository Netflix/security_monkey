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
from security_monkey.tests import SecurityMonkeyTestCase
from security_monkey.watcher import Watcher, ChangeItem
from security_monkey.datastore import Item, ItemAudit, Technology
from security_monkey.datastore import Account, AccountType, Datastore
from security_monkey import db


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
                          account_type_id=account_type_result.id)

        db.session.add(account)
        db.session.commit()
