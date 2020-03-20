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
from security_monkey.tests.watchers import SecurityMonkeyWatcherTestCase
from security_monkey.watchers.lambda_function import LambdaFunction
from security_monkey import AWS_DEFAULT_REGION

import boto3
from moto import mock_sts, mock_lambda
from freezegun import freeze_time
import io
import zipfile


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


class LambdaFunctionWatcherTestCase(SecurityMonkeyWatcherTestCase):

    @freeze_time("2016-07-18 12:00:00")
    @mock_sts
    @mock_lambda
    def test_slurp(self):
        conn = boto3.client('lambda', AWS_DEFAULT_REGION)

        conn.create_function(
            FunctionName='testFunction',
            Runtime='python3.7',
            Role='arn:aws:iam::123456789010:role/test-iam-role',
            Handler='lambda_function.handler',
            Code={
                'ZipFile': get_test_zip_file()
            },
            Description='test lambda function',
            Timeout=3,
            MemorySize=128,
            Publish=True,
        )
        watcher = LambdaFunction(accounts=[self.account.name])

        # Moto doesn't have all of lambda mocked out, so we can't test get_method, just list_method.
        def mock_get_method(item):
            item['arn:aws:iam::123456789010:role/test-iam-role'] = item['FunctionArn']
            return item

        watcher.get_method = lambda *args, **kwargs: mock_get_method(args[0])

        item_list, exception_map = watcher.slurp()
        

        self.assertIs(
            expr1=len(item_list),
            expr2=2,
            msg="Watcher should have 2 item but has {}".format(len(item_list)))
