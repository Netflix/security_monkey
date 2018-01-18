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
.. module: security_monkey.watchers.rds.rds_snapshot
    :platform: Unix

.. version:: $$VERSION$$
.. moduleauthor:: Bridgewater OSS <opensource@bwater.com>


"""
from security_monkey.watcher import Watcher
from security_monkey.watcher import ChangeItem
from security_monkey.constants import TROUBLE_REGIONS
from security_monkey.exceptions import BotoConnectionIssue
from security_monkey import app

from boto.rds import regions


class RDSSnapshot(Watcher):
    index = 'rdssnapshot'
    i_am_singular = 'RDS Snapshot'
    i_am_plural = 'RDS Snapshots'

    def __init__(self, accounts=None, debug=False):
        super(RDSSnapshot, self).__init__(accounts=accounts, debug=debug)

    def slurp(self):
        """
        :returns: item_list - list of RDS snapshots in use by account
        :returns: exception_map - A dict where the keys are a tuple containing the
            location of the exception and the value is the actual exception

        """
        self.prep_for_slurp()
        from security_monkey.common.sts_connect import connect
        item_list = []
        exception_map = {}
        for account in self.accounts:
            for region in regions():
                app.logger.debug(
                    "Checking {}/{}/{}".format(self.index, account, region.name))

                snapshots = []
                try:
                    rds = connect(account, 'boto3.rds.client', region=region)

                    marker = ''
                    while True:
                        response = self.wrap_aws_rate_limited_call(
                            rds.describe_db_snapshots,
                            Marker=marker)

                        snapshots.extend(response.get('DBSnapshots'))

                        if response.get('Marker'):
                            marker = response.get('Marker')
                        else:
                            break

                except Exception as e:
                    if region.name not in TROUBLE_REGIONS:
                        exc = BotoConnectionIssue(
                            str(e), self.index, account, region.name)
                        self.slurp_exception(
                            (self.index, account, region.name), exc, exception_map)
                    continue

                app.logger.debug("Found {} {}".format(
                    len(snapshots), self.i_am_plural))

                for snapshot in snapshots:

                    name = snapshot.get('DBSnapshotIdentifier')

                    if self.check_ignore_list(name):
                        continue

                    config = dict(snapshot)
                    config['InstanceCreateTime'] = str(config.get('InstanceCreateTime'))
                    config['SnapshotCreateTime'] = str(config.get('SnapshotCreateTime'))
                    config['Arn'] = str(config.get('DBSnapshotArn'))
                    config['Attributes'] = dict()

                    try:
                        attributes = self.wrap_aws_rate_limited_call(
                            rds.describe_db_snapshot_attributes,
                            DBSnapshotIdentifier=snapshot.get('DBSnapshotIdentifier'))

                        for attribute in attributes['DBSnapshotAttributesResult']['DBSnapshotAttributes']:
                            config['Attributes'][attribute['AttributeName']] = attribute['AttributeValues']

                    except Exception as e:
                        if region.name not in TROUBLE_REGIONS:
                            exc = BotoConnectionIssue(str(e), self.index, account, region.name)
                            self.slurp_exception((self.index, account, region.name, name), exc, exception_map)

                    item = RDSSnapshotItem(
                        region=region.name, account=account, name=name,
                        arn=snapshot.get('DBSnapshotArn'), config=dict(config), source_watcher=self)
                    item_list.append(item)

        return item_list, exception_map


class RDSSnapshotItem(ChangeItem):

    def __init__(self, region=None, account=None, name=None, arn=None, config=None, source_watcher=None):
        super(RDSSnapshotItem, self).__init__(
            index=RDSSnapshot.index,
            region=region,
            account=account,
            name=name,
            arn=arn,
            new_config=config if config else {},
            source_watcher=source_watcher)
