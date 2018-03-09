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
.. module: security_monkey.watchers.ec2.ebs_volume
    :platform: Unix

.. version:: $$VERSION$$
.. moduleauthor:: Bridgewater OSS <opensource@bwater.com>


"""
from security_monkey.decorators import record_exception, iter_account_region
from security_monkey.watcher import Watcher
from security_monkey.watcher import ChangeItem
from security_monkey import app


def volume_name(volume):
    name_tag = None
    if volume.get('Tags') is not None:
        for tag in volume.get('Tags'):
            if tag['Key'] == 'Name':
                name_tag = tag['Value']
                break

    if name_tag is not None:
        return name_tag + ' (' + volume.get('VolumeId') + ')'
    else:
        return volume.get('VolumeId')


def format_attachments(attachments=[]):
    """ Return formatted_attachments for volume config """
    formatted_attachments = []
    for attachment in attachments:
        formatted_attachment = {
            'attach_time': str(attachment.get('AttachTime')),
            'instance_id': attachment.get('InstanceId'),
            'volume_id': attachment.get('VolumeId'),
            'state': attachment.get('State'),
            'delete_on_termination': attachment.get('DeleteOnTermination'),
            'device': attachment.get('Device')
        }
        formatted_attachments.append(formatted_attachment)
    return formatted_attachments


def process_volume(volume, **kwargs):
    app.logger.debug("Slurping {index} ({name}) from {account}".format(
        index=EBSVolume.i_am_singular,
        name=kwargs['name'],
        account=kwargs['account_name'])
    )
    return {
        'name': kwargs['name'],
        'volume_id': volume.get('VolumeId'),
        'volume_type': volume.get('VolumeType'),
        'size': volume.get('Size'),
        'snapshot_id': volume.get('SnapshotId'),
        'create_time': str(volume.get('CreateTime')),
        'availability_zone': volume.get('AvailabilityZone'),
        'state': volume.get('State'),
        'encrypted': volume.get('Encrypted'),
        'attachments': format_attachments(volume.get('Attachments'))
    }


class EBSVolume(Watcher):
    index = 'ebsvolume'
    i_am_singular = 'EBS Volume'
    i_am_plural = 'EBS Volumes'

    def __init__(self, accounts=None, debug=False):
        super(EBSVolume, self).__init__(accounts=accounts, debug=debug)

    @record_exception()
    def describe_volumes(self, **kwargs):
        from security_monkey.common.sts_connect import connect
        ec2 = connect(kwargs['account_name'], 'boto3.ec2.client', region=kwargs['region'],
                      assumed_role=kwargs['assumed_role'])

        response = self.wrap_aws_rate_limited_call(ec2.describe_volumes)
        volumes = response.get('Volumes')
        return [volume for volume in volumes if not self.check_ignore_list(volume_name(volume))]

    def slurp(self):
        """
        :returns: item_list - list of EBS volumes in use by account
        :returns: exception_map - A dict where the keys are a tuple containing the
            location of the exception and the value is the actual exception

        """
        self.prep_for_slurp()

        @iter_account_region(index=self.index, accounts=self.accounts, service_name='ec2')
        def slurp_items(**kwargs):
            item_list = []
            exception_map = {}
            kwargs['exception_map'] = exception_map
            app.logger.debug("Checking {}/{}/{}".format(self.index,
                                                        kwargs['account_name'], kwargs['region']))
            volumes = self.describe_volumes(**kwargs)

            if volumes:
                app.logger.debug("Found {} {}".format(
                    len(volumes), self.i_am_plural))
                for volume in volumes:
                    kwargs['name'] = volume_name(volume)
                    config = process_volume(volume, **kwargs)

                    item = EBSVolumeItem(region=kwargs['region'],
                                         account=kwargs['account_name'],
                                         name=kwargs['name'], config=config, source_watcher=self)

                    item_list.append(item)

            return item_list, exception_map
        return slurp_items()


class EBSVolumeItem(ChangeItem):

    def __init__(self, region=None, account=None, name=None, config=None, source_watcher=None):
        super(EBSVolumeItem, self).__init__(
            index=EBSVolume.index,
            region=region,
            account=account,
            name=name,
            new_config=config if config else {},
            source_watcher=source_watcher)
