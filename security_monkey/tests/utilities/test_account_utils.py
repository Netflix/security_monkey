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
.. module: security_monkey.tests.utilities.test_account_utils
    :platform: Unix
.. version:: $$VERSION$$
.. moduleauthor::  Mike Grima <mgrima@netflix.com>
"""
from security_monkey.account_manager import bulk_enable_accounts, bulk_disable_accounts
from security_monkey.exceptions import AccountNameExists
from security_monkey.manage import AddAccount, manager
from security_monkey import db
from security_monkey.datastore import AccountType, Account, AccountTypeCustomValues
from security_monkey.tests import SecurityMonkeyTestCase


class AccountTestUtils(SecurityMonkeyTestCase):
    def pre_test_setup(self):
        self.account_type = AccountType(name='AWS')
        db.session.add(self.account_type)
        db.session.commit()

    def test_create_aws_account(self):
        from security_monkey.account_manager import account_registry

        for name, account_manager in list(account_registry.items()):
            manager.add_command("add_account_%s" % name.lower(), AddAccount(account_manager()))

        manager.handle("manage.py", ["add_account_aws", "-n", "test", "--active", "--id", "99999999999",
                                     "--canonical_id", "bcaf1ffd86f41161ca5fb16fd081034f",
                                     "--role_name", "SecurityMonkey"])

        account = Account.query.filter(Account.name == "test").first()
        assert account
        assert account.identifier == "99999999999"
        assert account.active
        assert len(account.custom_fields) == 4

        # Get the canonical ID field:
        c_id = AccountTypeCustomValues.query.filter(AccountTypeCustomValues.name == "canonical_id",
                                                    AccountTypeCustomValues.account_id == account.id).first()

        assert c_id
        assert c_id.value == "bcaf1ffd86f41161ca5fb16fd081034f"

        # Already exists:
        assert manager.handle("manage.py", ["add_account_aws", "-n", "test", "--active", "--id", "99999999999",
                                            "--canonical_id", "bcaf1ffd86f41161ca5fb16fd081034f",
                                            "--role_name", "SecurityMonkey"]) == -1

    def test_update_aws_account(self):
        from security_monkey.account_manager import account_registry

        for name, account_manager in list(account_registry.items()):
            manager.add_command("add_account_%s" % name.lower(), AddAccount(account_manager()))

        # Create the account:
        from security_monkey.account_manager import account_registry
        for name, am in list(account_registry.items()):
            if name == "AWS":
                break

        account_manager = am()
        account_manager.create(account_manager.account_type, "test", True, False, "Tests", "99999999999",
                               custom_fields=dict(canonical_id="bcaf1ffd86f41161ca5fb16fd081034f", s3_id=None))

        # Create a second account:
        account_manager.create(account_manager.account_type, "test2", True, False, "Tests", "99999999990",
                               custom_fields=dict(canonical_id="bcaf1ffd86f41161ca5fb16fd081asdf", s3_id=None))

        # Get the ID of the first account:
        id = Account.query.filter(Account.name == "test").one().id

        # Try to rename the account:
        account_manager.update(id, account_manager.account_type, "lololol", True, False, "Tests", "99999999999",
                               custom_fields=dict(canonical_id="bcaf1ffd86f41161ca5fb16fd081034f", s3_id=None))

        assert not Account.query.filter(Account.name == "test").first()
        assert Account.query.filter(Account.name == "lololol").first().id == id

        # Try to update it to an existing name:
        with self.assertRaises(AccountNameExists):
            account_manager.update(id, account_manager.account_type, "test2", True, False, "Tests", "99999999999",
                                   custom_fields=dict(canonical_id="bcaf1ffd86f41161ca5fb16fd081034f", s3_id=None))

    def test_disable_all_accounts(self):
        bulk_disable_accounts(['TEST_ACCOUNT1', 'TEST_ACCOUNT2', 'TEST_ACCOUNT3', 'TEST_ACCOUNT4'])
        accounts = Account.query.all()
        for account in accounts:
            self.assertFalse(account.active)

    def test_disable_one_accounts(self):
        bulk_disable_accounts(['TEST_ACCOUNT1'])
        accounts = Account.query.all()
        for account in accounts:
            if account.name == 'TEST_ACCOUNT2':
                self.assertTrue(account.active)
            else:
                self.assertFalse(account.active)

    def test_enable_all_accounts(self):
        bulk_enable_accounts(['TEST_ACCOUNT1', 'TEST_ACCOUNT2', 'TEST_ACCOUNT3', 'TEST_ACCOUNT4'])
        accounts = Account.query.all()
        for account in accounts:
            self.assertTrue(account.active)

    def test_enable_one_accounts(self):
        bulk_enable_accounts(['TEST_ACCOUNT3'])
        accounts = Account.query.all()
        for account in accounts:
            if account.name != 'TEST_ACCOUNT4':
                self.assertTrue(account.active)
            else:
                self.assertFalse(account.active)

    def test_enable_bad_accounts(self):
        bulk_enable_accounts(['BAD_ACCOUNT'])
        accounts = Account.query.all()
        for account in accounts:
            if account.name == 'TEST_ACCOUNT1' or account.name == 'TEST_ACCOUNT2':
                self.assertTrue(account.active)
            else:
                self.assertFalse(account.active)

    def test_disable_bad_accounts(self):
        bulk_disable_accounts(['BAD_ACCOUNT'])
        accounts = Account.query.all()
        for account in accounts:
            if account.name == 'TEST_ACCOUNT1' or account.name == 'TEST_ACCOUNT2':
                self.assertTrue(account.active)
            else:
                self.assertFalse(account.active)
