#     Copyright 2017 Netflix, Inc.
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
.. module: security_monkey.tests.watchers.test_datastore_utils
    :platform: Unix
.. version:: $$VERSION$$
.. moduleauthor::  Mike Grima <mgrima@netflix.com>
"""
import json

from security_monkey.datastore import Account, Technology, AccountType, ItemAudit
from security_monkey.tests import SecurityMonkeyTestCase, db
from security_monkey.watcher import ChangeItem

ACTIVE_CONF = {
    "account_number": "012345678910",
    "technology": "iamrole",
    "region": "universal",
    "name": "SomeRole",
    "policy": {
        "Statement": [
            {
                "Effect": "Allow",
                "Action": "*",
                "Resource": "*"
            }
        ]
    },
    "Arn": "arn:aws:iam::012345678910:role/SomeRole"
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


class SomeWatcher:
    def __init__(self):
        self.ephemeral_paths = []


class DatabaseUtilsTestCase(SecurityMonkeyTestCase):
    def pre_test_setup(self):
        pass

    def setup_db(self):
        account_type_result = AccountType(name='AWS')
        db.session.add(account_type_result)
        db.session.commit()

        self.account = Account(identifier="012345678910", name="testing",
                               account_type_id=account_type_result.id)
        self.technology = Technology(name="iamrole")

        db.session.add(self.account)
        db.session.add(self.technology)
        db.session.commit()

    def test_is_active(self):
        from security_monkey.datastore_utils import is_active

        not_active = {"Arn": "arn:aws:iam::012345678910:role/someDeletedRole"}
        assert not is_active(not_active)

        still_not_active = {
            "account_number": "012345678910",
            "technology": "iamrole",
            "region": "universal",
            "name": "somethingThatWasDeleted"
        }
        assert not is_active(still_not_active)

        assert is_active(ACTIVE_CONF)

    def test_create_revision(self):
        from security_monkey.datastore_utils import create_revision
        from security_monkey.datastore import Item

        self.setup_db()

        db_item = Item(region="universal",
                       name="SomeRole",
                       arn="arn:aws:iam::012345678910:role/SomeRole",
                       tech_id=self.technology.id,
                       account_id=self.account.id
                       )
        db.session.add(db_item)
        db.session.commit()

        revision = create_revision(ACTIVE_CONF, db_item)
        assert revision
        assert revision.active
        assert json.dumps(revision.config) == json.dumps(ACTIVE_CONF)
        assert revision.item_id == db_item.id

    def test_create_item_aws(self):
        from security_monkey.datastore_utils import create_item_aws

        self.setup_db()

        sti = SomeTestItem.from_slurp(ACTIVE_CONF, account_name=self.account.name)

        item = create_item_aws(sti, self.technology, self.account)
        assert item.region == "universal"
        assert item.name == "SomeRole"
        assert item.arn == "arn:aws:iam::012345678910:role/SomeRole"
        assert item.tech_id == self.technology.id
        assert item.account_id == self.account.id

    def test_hash_item(self):
        from security_monkey.datastore_utils import hash_item
        test_config = {
            "SomeDurableProp": "is some value",
            "ephemeralPath": "some thing that changes",
            "some_area": {
                "some_nested_place": {
                    "Durable": True
                },
                "ephemeral": True
            }
        }

        ephemeral_paths = [
            "ephemeralPath",
            "some_area*$ephemeral"
        ]

        # Ran the first time -- verified that this is correct:
        original_complete_hash = "85b8874a7ca98d7f5f4587d80d310bc5"
        durable_hash = "1d1d718ea820b14f620f5262ae6d06fb"

        assert hash_item(test_config, ephemeral_paths) == (original_complete_hash, durable_hash)

        # Change a durable value:
        test_config["SomeDurableProp"] = "is some OTHER value"
        assert hash_item(test_config, ephemeral_paths) != (original_complete_hash, durable_hash)

        # Go back:
        test_config["SomeDurableProp"] = "is some value"
        assert hash_item(test_config, ephemeral_paths) == (original_complete_hash, durable_hash)

        # Change ephemeral values:
        test_config["ephemeralPath"] = "askldjfpwojf0239f32"
        test_ephemeral = hash_item(test_config, ephemeral_paths)
        assert test_ephemeral[0] != original_complete_hash
        assert test_ephemeral[1] == durable_hash

    def test_result_from_item(self):
        from security_monkey.datastore_utils import result_from_item
        from security_monkey.datastore import Item

        self.setup_db()

        item = Item(region="universal",
                    name="SomeRole",
                    arn="arn:aws:iam::012345678910:role/SomeRole",
                    tech_id=self.technology.id,
                    account_id=self.account.id
                    )

        # This is actually what is passed into result_from_item:
        sti = SomeTestItem().from_slurp(ACTIVE_CONF, account_name=self.account.name)

        assert not result_from_item(sti, self.account, self.technology)

        db.session.add(item)
        db.session.commit()

        assert result_from_item(sti, self.account, self.technology).id == item.id

    def test_detect_change(self):
        from security_monkey.datastore_utils import detect_change, hash_item
        from security_monkey.datastore import Item

        self.setup_db()

        item = Item(region="universal",
                    name="SomeRole",
                    arn="arn:aws:iam::012345678910:role/SomeRole",
                    tech_id=self.technology.id,
                    account_id=self.account.id,
                    )

        sti = SomeTestItem().from_slurp(ACTIVE_CONF, account_name=self.account.name)

        # Get the hash:
        complete_hash, durable_hash = hash_item(sti.config, [])

        # Item does not exist in the DB yet:
        assert (True, 'durable', None, 'created') == detect_change(sti, self.account, self.technology, complete_hash,
                                                        durable_hash)

        # Add the item to the DB:
        db.session.add(item)
        db.session.commit()

        # Durable change (nothing hashed in DB yet)
        assert (True, 'durable', item, 'changed') == detect_change(sti, self.account, self.technology, complete_hash,
                                                        durable_hash)

        # No change:
        item.latest_revision_complete_hash = complete_hash
        item.latest_revision_durable_hash = durable_hash
        db.session.add(item)
        db.session.commit()

        assert (False, None, item, None) == detect_change(sti, self.account, self.technology, complete_hash,
                                                    durable_hash)

        # Ephemeral change:
        mod_conf = dict(ACTIVE_CONF)
        mod_conf["IGNORE_ME"] = "I am ephemeral!"
        complete_hash, durable_hash = hash_item(mod_conf, ["IGNORE_ME"])

        assert (True, 'ephemeral', item, None) == detect_change(sti, self.account, self.technology, complete_hash,
                                                          durable_hash)

    def test_persist_item(self):
        from security_monkey.datastore_utils import persist_item, hash_item, result_from_item

        self.setup_db()

        sti = SomeTestItem().from_slurp(ACTIVE_CONF, account_name=self.account.name)

        # Get the hash:
        complete_hash, durable_hash = hash_item(sti.config, [])

        # Persist a durable change:
        persist_item(sti, None, self.technology, self.account, complete_hash, durable_hash, True)

        db_item = result_from_item(sti, self.account, self.technology)
        assert db_item
        assert db_item.revisions.count() == 1
        assert db_item.latest_revision_durable_hash == durable_hash == complete_hash
        assert db_item.latest_revision_complete_hash == complete_hash == durable_hash

        # No changes:
        persist_item(sti, db_item, self.technology, self.account, complete_hash, durable_hash, True)
        db_item = result_from_item(sti, self.account, self.technology)
        assert db_item
        assert db_item.revisions.count() == 1
        assert db_item.latest_revision_durable_hash == complete_hash == durable_hash
        assert db_item.latest_revision_complete_hash == complete_hash == durable_hash

        # Ephemeral change:
        mod_conf = dict(ACTIVE_CONF)
        mod_conf["IGNORE_ME"] = "I am ephemeral!"
        new_complete_hash, new_durable_hash = hash_item(mod_conf, ["IGNORE_ME"])
        sti = SomeTestItem().from_slurp(mod_conf, account_name=self.account.name)
        persist_item(sti, db_item, self.technology, self.account, new_complete_hash, new_durable_hash, False)

        db_item = result_from_item(sti, self.account, self.technology)
        assert db_item
        assert db_item.revisions.count() == 1
        assert db_item.latest_revision_durable_hash == new_durable_hash == durable_hash
        assert db_item.latest_revision_complete_hash == new_complete_hash != complete_hash

    def test_inactivate_old_revisions(self):
        from security_monkey.datastore_utils import inactivate_old_revisions, hash_item, persist_item, result_from_item
        from security_monkey.datastore import ItemRevision, Item

        self.setup_db()

        # Need to create 3 items first before we can test deletions:
        for x in range(0, 3):
            modConf = dict(ACTIVE_CONF)
            modConf["name"] = "SomeRole{}".format(x)
            modConf["Arn"] = "arn:aws:iam::012345678910:role/SomeRole{}".format(x)

            sti = SomeTestItem().from_slurp(modConf, account_name=self.account.name)

            # Get the hash:
            complete_hash, durable_hash = hash_item(sti.config, [])

            # persist:
            persist_item(sti, None, self.technology, self.account, complete_hash, durable_hash, True)

            db_item = result_from_item(sti, self.account, self.technology)

            # Add issues for these items: (just add two for testing purposes)
            db.session.add(ItemAudit(score=10,
                                     issue="IAM Role has full admin permissions.",
                                     notes=json.dumps(sti.config),
                                     item_id=db_item.id))
            db.session.add(ItemAudit(score=9001, issue="Some test issue", notes="{}", item_id=db_item.id))

        db.session.commit()

        # Now, actually test for deleted revisions:
        arns = [
            "arn:aws:iam::012345678910:role/SomeRole",  # <-- Does not exist in the list
            "arn:aws:iam::012345678910:role/SomeRole0",  # <-- Does exist -- should not get deleted
        ]

        inactivate_old_revisions(SomeWatcher(), arns, self.account, self.technology)

        # Check that SomeRole1 and SomeRole2 are marked as inactive:
        for x in range(1, 3):
            item_revision = ItemRevision.query.join((Item, ItemRevision.id == Item.latest_revision_id)).filter(
                Item.arn == "arn:aws:iam::012345678910:role/SomeRole{}".format(x),
            ).one()

            assert not item_revision.active

        # Check that the SomeRole0 is still OK:
        item_revision = ItemRevision.query.join((Item, ItemRevision.id == Item.latest_revision_id)).filter(
            Item.arn == "arn:aws:iam::012345678910:role/SomeRole0").one()

        assert len(ItemAudit.query.filter(ItemAudit.item_id == item_revision.item_id).all()) == 2

        assert item_revision.active
