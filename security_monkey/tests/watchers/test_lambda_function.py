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
.. module: security_monkey.tests.watchers.test_lambda_function
    :platform: Unix

.. version:: $$VERSION$$
.. moduleauthor:: Bridgewater OSS <opensource@bwater.com>


"""
from security_monkey.tests import SecurityMonkeyTestCase
from security_monkey.watchers.lambda_function import LambdaFunction
from security_monkey.datastore import Account
from security_monkey.tests.db_mock import MockAccountQuery

import boto3
from moto import mock_sts, mock_lambda
from freezegun import freeze_time
from mock import patch
import io
import zipfile

mock_query = MockAccountQuery()


def get_test_zip_file():
    zip_output = io.BytesIO()
    zip_file = zipfile.ZipFile(zip_output, 'w')
    zip_file.writestr('lambda_function.py', b'''\
def handler(event, context):
    return "hello world"
''')
    zip_file.close()
    zip_output.seek(0)
    return zip_output.read()


class LambdaFunctionWatcherTestCase(SecurityMonkeyTestCase):

    @freeze_time("2016-07-18 12:00:00")
    @mock_sts
    @mock_lambda
    @patch('security_monkey.datastore.Account.query', new=mock_query)
    def test_slurp(self):
        test_account = Account()
        test_account.name = "TEST_ACCOUNT"
        test_account.notes = "TEST ACCOUNT"
        test_account.s3_name = "TEST_ACCOUNT"
        test_account.number = "012345678910"
        test_account.role_name = "TEST_ACCOUNT"
        mock_query.add_account(test_account)

        conn = boto3.client('lambda', 'us-east-1')

        conn.create_function(
            FunctionName='testFunction',
            Runtime='python2.7',
            Role='test-iam-role',
            Handler='lambda_function.handler',
            Code={
                'ZipFile': get_test_zip_file()
            },
            Description='test lambda function',
            Timeout=3,
            MemorySize=128,
            Publish=True,
        )
        watcher = LambdaFunction(accounts=[test_account.name])
        item_list, exception_map = watcher.slurp()

        self.assertIs(
            expr1=len(item_list),
            expr2=1,
            msg="Watcher should have 1 item but has {}".format(len(item_list)))
