#     Copyright 2014 Netflix, Inc.
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
.. module: security_monkey.tests.watchers.test_s3
    :platform: Unix
.. version:: $$VERSION$$
.. moduleauthor::  Mike Grima <mgrima@netflix.com>
"""
import boto3
from moto import mock_s3
from moto import mock_sts

from security_monkey.watchers.s3 import S3
from security_monkey.datastore import Account, Technology, Item, ExceptionLogs, AccountType
from security_monkey.tests import SecurityMonkeyTestCase, db


class S3TestCase(SecurityMonkeyTestCase):
    def pre_test_setup(self):
        account_type_result = AccountType.query.filter(AccountType.name == 'AWS').first()
        if not account_type_result:
            account_type_result = AccountType(name='AWS')
            db.session.add(account_type_result)
            db.session.commit()

        self.account = Account(identifier="012345678910", name="testing",
                               active=True, third_party=False,
                               account_type_id=account_type_result.id)
        self.technology = Technology(name="s3")
        self.item = Item(region="us-west-2", name="somebucket",
                         arn="arn:aws:s3:::somebucket", technology=self.technology,
                         account=self.account)

        db.session.add(self.account)
        db.session.add(self.technology)
        db.session.add(self.item)

        db.session.commit()

        mock_s3().start()
        client = boto3.client("s3")
        client.create_bucket(Bucket="somebucket")
        client.create_bucket(Bucket="someotherbucket")
        client.create_bucket(Bucket="someotherbucket2")

    def test_watcher_exceptions(self):
        """
        Tests that if exceptions are encountered, the watcher continues.

        Unfortunately -- moto lacks all of the S3 methods that we need. So this is just a
        test to ensure that exception handling works OK.
        :return:
        """
        mock_sts().start()

        s3_watcher = S3(accounts=[self.account.name])
        s3_watcher.slurp()

        assert len(ExceptionLogs.query.all()) == 3  # We created 3 buckets

        mock_s3().stop()
        mock_sts().stop()
