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
.. module: security_monkey.tests.watchers.ec2.test_ec2_image
    :platform: Unix

.. version:: $$VERSION$$
.. moduleauthor:: Bridgewater OSS <opensource@bwater.com>


"""
from security_monkey.tests.watchers import SecurityMonkeyWatcherTestCase
from security_monkey.watchers.ec2.ec2_image import EC2Image
from security_monkey import AWS_DEFAULT_REGION

import boto3
from moto import mock_sts, mock_ec2
from freezegun import freeze_time


class EC2ImageWatcherTestCase(SecurityMonkeyWatcherTestCase):

    @freeze_time("2016-07-18 12:00:00")
    @mock_sts
    @mock_ec2
    def test_slurp(self):
        def get_method(*args, **kwargs):
            if kwargs['region'] == 'us-east-1':
                return {'Arn': 'somearn', 'ImageId': 'ami-1234abcd'}
            return {}
        def list_method(*args, **kwargs):
            if kwargs['region'] == 'us-east-1':
                return [{'Arn': 'somearn', 'ImageId': 'ami-1234abcd'}]
            return []

        EC2Image.get_method = lambda *args, **kwargs: get_method(*args, **kwargs)
        EC2Image.list_method = lambda *args, **kwargs: list_method(*args, **kwargs)

        watcher = EC2Image(accounts=[self.account.name])
        item_list, exception_map = watcher.slurp()

        self.assertIs(
            expr1=len(item_list),
            expr2=1,
            msg="Watcher should have 1 item but has {}".format(len(item_list)))
