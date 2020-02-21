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
.. module: security_monkey.tests.watchers.test_iam_role
    :platform: Unix
.. version:: $$VERSION$$
.. moduleauthor::  Mike Grima <mgrima@netflix.com>
"""
import json

import boto3
from moto import mock_iam
from moto import mock_sts

from security_monkey.datastore import Account, Technology, ExceptionLogs, AccountType, IgnoreListEntry
from security_monkey.tests import SecurityMonkeyTestCase, db
from security_monkey.watchers.iam.iam_role import IAMRole
from security_monkey import ARN_PREFIX


class IAMRoleTestCase(SecurityMonkeyTestCase):
    def pre_test_setup(self):
        account_type_result = AccountType(name='AWS')
        db.session.add(account_type_result)
        db.session.commit()

        self.account = Account(identifier="012345678910", name="testing",
                               third_party=False, active=True,
                               account_type_id=account_type_result.id)
        self.technology = Technology(name="iamrole")

        self.total_roles = 75

        db.session.add(self.account)
        db.session.add(self.technology)
        db.session.commit()
        mock_iam().start()
        client = boto3.client("iam")

        aspd = {
            "Version": "2012-10-17",
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

        policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Deny",
                    "Action": "*",
                    "Resource": "*"
                }
            ]
        }

        for x in range(0, self.total_roles):
            # Create the IAM Role via Moto:
            aspd["Statement"][0]["Resource"] = ARN_PREFIX + "arn:aws:iam:012345678910:role/roleNumber{}".format(x)
            client.create_role(Path="/", RoleName="roleNumber{}".format(x),
                               AssumeRolePolicyDocument=json.dumps(aspd, indent=4))
            client.put_role_policy(RoleName="roleNumber{}".format(x), PolicyName="testpolicy",
                                   PolicyDocument=json.dumps(policy, indent=4))

    def test_slurp_list(self):
        mock_sts().start()

        watcher = IAMRole(accounts=[self.account.name])

        _, exceptions = watcher.slurp_list()

        assert len(exceptions) == 0
        assert len(watcher.total_list) == self.total_roles
        assert not watcher.done_slurping


    def test_empty_slurp_list(self):
        mock_sts().start()

        watcher = IAMRole(accounts=[self.account.name])
        watcher.list_method = lambda **kwargs: []

        _, exceptions = watcher.slurp_list()
        assert len(exceptions) == 0
        assert len(watcher.total_list) == 0
        assert watcher.done_slurping


    def test_slurp_list_exceptions(self):
        mock_sts().start()

        watcher = IAMRole(accounts=[self.account.name])

        def raise_exception():
            raise Exception("LOL, HAY!")

        watcher.list_method = lambda **kwargs: raise_exception()

        _, exceptions = watcher.slurp_list()
        assert len(exceptions) == 1
        assert len(ExceptionLogs.query.all()) == 1


    def test_slurp_items(self):
        mock_sts().start()

        watcher = IAMRole(accounts=[self.account.name])

        # Or else this will take forever:
        watcher.batched_size = 10
        watcher.slurp_list()

        items, exceptions = watcher.slurp()
        assert len(exceptions) == 0
        assert self.total_roles > len(items) == watcher.batched_size
        assert watcher.batch_counter == 1

        # Slurp again:
        items, exceptions = watcher.slurp()
        assert len(exceptions) == 0
        assert self.total_roles > len(items) == watcher.batched_size
        assert watcher.batch_counter == 2



    def test_slurp_items_with_exceptions(self):
        mock_sts().start()

        watcher = IAMRole(accounts=[self.account.name])

        # Or else this will take forever:
        watcher.batched_size = 10
        watcher.slurp_list()

        def raise_exception():
            raise Exception("LOL, HAY!")

        watcher.get_method = lambda *args, **kwargs: raise_exception()

        items, exceptions = watcher.slurp()

        assert len(exceptions) == watcher.batched_size
        assert len(items) == 0
        assert watcher.batch_counter == 1


class IAMRoleSkipTestCase(SecurityMonkeyTestCase):
    def pre_test_setup(self):
        account_type_result = AccountType(name='AWS')
        db.session.add(account_type_result)
        db.session.commit()

        self.account = Account(identifier="012345678910", name="testing",
                               third_party=False, active=True,
                               account_type_id=account_type_result.id)
        self.technology = Technology(name="iamrole")

        self.total_roles = 10

        db.session.add(self.account)
        db.session.add(self.technology)
        db.session.commit()
        mock_iam().start()
        client = boto3.client("iam")

        aspd = {
            "Version": "2012-10-17",
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

        policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Deny",
                    "Action": "*",
                    "Resource": "*"
                }
            ]
        }

        for x in range(0, self.total_roles):
            # Create the IAM Role via Moto:
            aspd["Statement"][0]["Resource"] = ARN_PREFIX + "arn:aws:iam:012345678910:role/roleNumber{}".format(x)
            client.create_role(Path="/", RoleName="roleNumber{}".format(x),
                               AssumeRolePolicyDocument=json.dumps(aspd, indent=4))
            client.put_role_policy(RoleName="roleNumber{}".format(x), PolicyName="testpolicy",
                                   PolicyDocument=json.dumps(policy, indent=4))

    def test_slurp_items_with_skipped(self):
        mock_sts().start()

        watcher = IAMRole(accounts=[self.account.name])

        watcher.batched_size = 5
        watcher.slurp_list()

        watcher.ignore_list = [
            IgnoreListEntry(prefix="roleNumber0"),
            IgnoreListEntry(prefix="roleNumber1"),
            IgnoreListEntry(prefix="roleNumber6")
        ]

        first_batch, exceptions = watcher.slurp()
        item_sum = len(first_batch)
        assert len(exceptions) == 0
        assert watcher.batch_counter == 1

        batch_lookup = {}   # Ensure we aren't processing duplicates
        for r in first_batch:
            assert r.name not in watcher.ignore_list    # Ensure we properly ignore the things
            batch_lookup[r.name] = True

        # Slurp again:
        second_batch, exceptions = watcher.slurp()
        item_sum += len(second_batch)
        assert len(exceptions) == 0
        assert watcher.batch_counter == 2

        for r in second_batch:
            assert r.name not in watcher.ignore_list
            assert not batch_lookup.get(r.name)
            batch_lookup[r.name] = True

        # Sum of items should be total items - length of the ignored items:
        assert self.total_roles - len(watcher.ignore_list) == item_sum == len(batch_lookup)
