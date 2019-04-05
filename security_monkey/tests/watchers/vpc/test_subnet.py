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
.. module: security_monkey.tests.watchers.vpc.test_subnet
    :platform: Unix

.. version:: $$VERSION$$
.. moduleauthor:: Bridgewater OSS <opensource@bwater.com>


"""
from security_monkey.tests.watchers import SecurityMonkeyWatcherTestCase
from security_monkey.watchers.vpc.subnet import Subnet

import boto
from moto import mock_sts, mock_ec2_deprecated
from freezegun import freeze_time


class SubnetWatcherTestCase(SecurityMonkeyWatcherTestCase):

    @freeze_time("2017-02-13 12:00:00")
    @mock_sts
    @mock_ec2_deprecated
    def test_slurp(self):
        conn = boto.connect_vpc('the_key', 'the secret')
        vpc = conn.create_vpc("10.0.0.0/16")

        conn.create_subnet(vpc.id, "10.0.0.0/18")

        watcher = Subnet(accounts=[self.account.name])
        item_list, exception_map = watcher.slurp()

        vpc_ids = {subnet.config['vpc_id'] for subnet in item_list}
        self.assertIn(vpc.id, vpc_ids)
