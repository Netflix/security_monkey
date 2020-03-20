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
.. module: security_monkey.tests.utilities.test_s3_canonical
    :platform: Unix
.. version:: $$VERSION$$
.. moduleauthor::  Mike Grima <mgrima@netflix.com>
"""
from security_monkey.manage import fetch_aws_canonical_ids, AddAccount, manager
from security_monkey import db
from security_monkey.common.s3_canonical import get_canonical_ids
from security_monkey.datastore import AccountType, Account, ExceptionLogs, AccountTypeCustomValues
from security_monkey.tests import SecurityMonkeyTestCase

from moto import mock_sts, mock_s3

import boto3


class S3CanonicalTestCase(SecurityMonkeyTestCase):
    def pre_test_setup(self):
        self.account_type = AccountType(name='AWS')
        db.session.add(self.account_type)
        db.session.commit()

        for x in range(0, 9):
            db.session.add(Account(name="account{}".format(x), account_type_id=self.account_type.id,
                                   identifier="01234567891{}".format(x), active=True))

        db.session.commit()

        mock_sts().start()
        mock_s3().start()

        self.s3_client = boto3.client("s3")
        self.s3_client.create_bucket(Bucket="testBucket")

    def test_get_canonical_ids(self):
        accounts = Account.query.all()
        get_canonical_ids(accounts)

        for account in accounts:
            assert len(account.custom_fields) == 1
            assert account.custom_fields[0].name == "canonical_id"
            assert account.custom_fields[0].value == "bcaf1ffd86f41161ca5fb16fd081034f"  # Default from moto.

            # Make it something else to test overrides:
            account.custom_fields[0].value = "replaceme"
            db.session.add(account)

        db.session.commit()

        # Test without override (nothing should be changed):
        get_canonical_ids(accounts)
        for account in accounts:
            assert len(account.custom_fields) == 1
            assert account.custom_fields[0].name == "canonical_id"
            assert account.custom_fields[0].value == "replaceme"

        # Test override:
        get_canonical_ids(accounts, override=True)
        for account in accounts:
            assert len(account.custom_fields) == 1
            assert account.custom_fields[0].name == "canonical_id"
            assert account.custom_fields[0].value == "bcaf1ffd86f41161ca5fb16fd081034f"  # Default from moto.

        #mock_sts().stop()
        #mock_s3().stop()

    def test_fetch_aws_canonical_ids_command(self):
        accounts = Account.query.all()
        fetch_aws_canonical_ids(False)

        for account in accounts:
            assert len(account.custom_fields) == 1
            assert account.custom_fields[0].name == "canonical_id"
            assert account.custom_fields[0].value == "bcaf1ffd86f41161ca5fb16fd081034f"  # Default from moto.

            # Make it something else to test overrides:
            account.custom_fields[0].value = "replaceme"
            db.session.add(account)

        db.session.commit()

        # Test without override (nothing should be changed):
        fetch_aws_canonical_ids(False)
        for account in accounts:
            assert len(account.custom_fields) == 1
            assert account.custom_fields[0].name == "canonical_id"
            assert account.custom_fields[0].value == "replaceme"

        # Test override:
        fetch_aws_canonical_ids(True)
        for account in accounts:
            assert len(account.custom_fields) == 1
            assert account.custom_fields[0].name == "canonical_id"
            assert account.custom_fields[0].value == "bcaf1ffd86f41161ca5fb16fd081034f"  # Default from moto.

        # Create an inactive account:
        inactive = Account(name="inactive", account_type_id=self.account_type.id,
                           identifier="109876543210")
        db.session.add(inactive)
        db.session.commit()

        # Run the change again:
        fetch_aws_canonical_ids(True)

        # Ensure that nothing happened to the inactive account:
        assert len(inactive.custom_fields) == 0

        # Also verify that no exceptions were encountered:
        assert len(ExceptionLogs.query.all()) == 0

        #mock_sts().stop()
        #mock_s3().stop()

    def test_create_account_with_canonical(self):
        from security_monkey.account_manager import account_registry

        for name, account_manager in list(account_registry.items()):
            manager.add_command("add_account_%s" % name.lower(), AddAccount(account_manager()))

        manager.handle("manage.py", ["add_account_aws", "-n", "test", "--active", "--id", "99999999999",
                                     "--canonical_id", "bcaf1ffd86f41161ca5fb16fd081034f", "--s3_name", "test",
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

        assert manager.handle("manage.py", ["add_account_aws", "-n", "test", "--active", "--id", "99999999999",
                                            "--canonical_id", "bcaf1ffd86f41161ca5fb16fd081034f", "--s3_name", "test",
                                            "--role_name", "SecurityMonkey"]) == -1

    def test_update_account_with_canonical(self):
        from security_monkey.account_manager import account_registry

        for name, account_manager in list(account_registry.items()):
            manager.add_command("add_account_%s" % name.lower(), AddAccount(account_manager()))

        # Update:
        manager.handle("manage.py", ["add_account_aws", "-n", "account0", "--active", "--id", "012345678910",
                                     "--canonical_id", "bcaf1ffd86f41161ca5fb16fd081034f", "--s3_name", "test",
                                     "--role_name", "SecurityMonkey", "--update-existing"])

        account = Account.query.filter(Account.name == "account0").first()
        assert account
        assert account.identifier == "012345678910"
        assert account.active
        assert len(account.custom_fields) == 4

        # Get the canonical ID field:
        c_id = AccountTypeCustomValues.query.filter(AccountTypeCustomValues.name == "canonical_id",
                                                    AccountTypeCustomValues.account_id == account.id).first()

        assert c_id
        assert c_id.value == "bcaf1ffd86f41161ca5fb16fd081034f"
