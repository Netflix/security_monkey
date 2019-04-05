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
.. module: security_monkey.watchers.ec2.ebs_snapshot
    :platform: Unix

.. version:: $$VERSION$$
.. moduleauthor:: Bridgewater OSS <opensource@bwater.com>


"""
from security_monkey.decorators import record_exception, iter_account_region
from security_monkey.watcher import Watcher
from security_monkey.watcher import ChangeItem
from security_monkey import app
import datetime


def snapshot_name(snapshot):
    name_tag = None
    if snapshot.get('Tags') is not None:
        for tag in snapshot.get('Tags'):
            if tag['Key'] == 'Name':
                name_tag = tag['Value']
                break

    if name_tag is not None:
        return name_tag + ' (' + snapshot.get('SnapshotId') + ')'
    else:
        return snapshot.get('SnapshotId')


class EBSSnapshot(Watcher):
    index = 'ebssnapshot'
    i_am_singular = 'EBS Snapshot'
    i_am_plural = 'EBS Snapshots'

    def __init__(self, accounts=None, debug=False):
        super(EBSSnapshot, self).__init__(accounts=accounts, debug=debug)

        # naive single entry cache
        self.last_session = None
        self.last_session_account = None
        self.last_session_region = None
        self.last_session_datetime = None

    def get_session(self, **kwargs):
        # cache the session for performance,
        # but expect it to be expired if it is over 45 minutes old
        if kwargs['account_name'] == self.last_session_account:
            if kwargs['region'] == self.last_session_region:
                if self.last_session_datetime:
                    if self.last_session_datetime > datetime.datetime.now() - datetime.timedelta(minutes=45):
                        return self.last_session

        from security_monkey.common.sts_connect import connect
        self.last_session = connect(kwargs['account_name'],
            'boto3.ec2.client',
            region=kwargs['region'],
            assumed_role=kwargs['assumed_role'])

        self.last_session_account = kwargs['account_name']
        self.last_session_region = kwargs['region']
        self.last_session_datetime = datetime.datetime.now()
        return self.last_session

    def get_attribute(self, attribute_name, result_key_name, snapshot, **kwargs):
        ec2 = self.get_session(**kwargs)
        attributes = self.wrap_aws_rate_limited_call(
            ec2.describe_snapshot_attribute,
            Attribute=attribute_name,
            SnapshotId=snapshot.get('SnapshotId'),
            DryRun=False)
        return attributes.get(result_key_name)

    @record_exception()
    def process_snapshot(self, snapshot, **kwargs):
        app.logger.debug("Slurping {index} ({name}) from {account}".format(
            index=EBSSnapshot.i_am_singular,
            name=kwargs['name'],
            account=kwargs['account_name']))

        return {
            'create_volume_permissions': self.get_attribute('createVolumePermission', 'CreateVolumePermissions', snapshot, **kwargs),
            'product_codes': self.get_attribute('productCodes', 'ProductCodes', snapshot, **kwargs),
            'name': snapshot_name(snapshot),
            'snapshot_id': snapshot.get('SnapshotId'),
            'volume_id': snapshot.get('VolumeId'),
            'state': snapshot.get('State'),
            'state_message': snapshot.get('StateMessage'),
            'start_time': str(snapshot.get('StartTime')),
            'progress': snapshot.get('Progress'),
            'ownerId': snapshot.get('OwnerId'),
            'description': snapshot.get('Description'),
            'volume_size': snapshot.get('VolumeSize'),
            'owner_alias': snapshot.get('OwnerAlias'),
            'tags': snapshot.get('Tags', []),
            'encrypted': snapshot.get('Encrypted', False),
            'kms_key_id': snapshot.get('KmsKeyId'),
            'data_encryption_key_id': snapshot.get('DataEncryptionKeyId'),
        }

    @record_exception()
    def describe_snapshots(self, **kwargs):
        ec2 = self.get_session(**kwargs)
        response = self.wrap_aws_rate_limited_call(ec2.describe_snapshots, OwnerIds=['self'])
        snapshots = response.get('Snapshots')
        return [snapshot for snapshot in snapshots if not self.check_ignore_list(snapshot_name(snapshot))]


    def slurp(self):
        """
        :returns: item_list - list of available EBS snapshots defined by account
        :returns: exception_map - A dict where the keys are a tuple containing the
            location of the exception and the value is the actual exception

        """
        self.prep_for_slurp()

        @iter_account_region(index=self.index, accounts=self.accounts, service_name='ec2')
        def slurp_items(**kwargs):
            item_list = []
            exception_map = {}
            kwargs['exception_map'] = exception_map
            app.logger.debug("Checking {}/{}/{}".format(self.index, kwargs['account_name'], kwargs['region']))
            snapshots = self.describe_snapshots(**kwargs)

            if snapshots:
                app.logger.debug("Found {} {}.".format(len(snapshots), self.i_am_plural))
                for snapshot in snapshots:
                    kwargs['name'] = snapshot_name(snapshot)
                    config = self.process_snapshot(snapshot, **kwargs)

                    item = EBSSnapshotItem(region=kwargs['region'],
                                           account=kwargs['account_name'],
                                           name=kwargs['name'], config=config, source_watcher=self)

                    item_list.append(item)

            return item_list, exception_map
        return slurp_items()


class EBSSnapshotItem(ChangeItem):

    def __init__(self, region=None, account=None, name=None, config=None, source_watcher=None):
        super(EBSSnapshotItem, self).__init__(
            index=EBSSnapshot.index,
            region=region,
            account=account,
            name=name,
            new_config=config if config else {},
            source_watcher=source_watcher)
