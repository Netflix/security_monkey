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
.. module: security_monkey.tests.watchers.ec2.test_ebs_snapshot
    :platform: Unix

.. version:: $$VERSION$$
.. moduleauthor:: Bridgewater OSS <opensource@bwater.com>


"""
from security_monkey.tests.watchers import SecurityMonkeyWatcherTestCase
from security_monkey.watchers.ec2.ebs_snapshot import EBSSnapshot
from security_monkey import AWS_DEFAULT_REGION

import boto
from moto import mock_sts_deprecated, mock_sts, mock_ec2_deprecated, mock_ec2
from freezegun import freeze_time


class EBSSnapshotWatcherTestCase(SecurityMonkeyWatcherTestCase):

    @freeze_time("2016-07-18 12:00:00")
    @mock_sts_deprecated
    @mock_ec2_deprecated
    @mock_sts
    @mock_ec2
    def test_slurp(self):
        conn = boto.connect_ec2('the_key', 'the_secret')
        vol = conn.create_volume(50, AWS_DEFAULT_REGION)
        conn.create_snapshot(vol.id, 'My snapshot')

        watcher = EBSSnapshot(accounts=[self.account.name])
        item_list, exception_map = watcher.slurp()

        descriptions = {snapshot.config['description'] for snapshot in item_list}
        self.assertIn('My snapshot', descriptions)
