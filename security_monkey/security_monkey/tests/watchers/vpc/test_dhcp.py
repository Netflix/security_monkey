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
.. module: security_monkey.tests.vpc.test_dhcp
    :platform: Unix

.. version:: $$VERSION$$
.. moduleauthor:: Bridgewater OSS <opensource@bwater.com>


"""
from security_monkey.tests.watchers import SecurityMonkeyWatcherTestCase
from security_monkey.watchers.vpc.dhcp import DHCP
from security_monkey import AWS_DEFAULT_REGION

import boto3
from moto import mock_sts, mock_ec2
from freezegun import freeze_time


class DHCPTestCase(SecurityMonkeyWatcherTestCase):

    @freeze_time("2016-07-18 12:00:00")
    @mock_sts
    @mock_ec2
    def test_slurp(self):
        ec2 = boto3.resource('ec2', region_name=AWS_DEFAULT_REGION)

        ec2.create_dhcp_options(DhcpConfigurations=[
            {'Key': 'domain-name', 'Values': ['example.com']},
            {'Key': 'domain-name-servers', 'Values': ['10.0.10.2']}
        ])

        watcher = DHCP(accounts=[self.account.name])
        item_list, exception_map = watcher.slurp()

        self.assertIs(
            expr1=len(item_list),
            expr2=1,
            msg="Watcher should have 1 item but has {}".format(len(item_list)))
