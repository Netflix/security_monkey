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
.. module: security_monkey.watchers.ec2instance
    :platform: Unix

.. version:: $$VERSION$$


"""
from security_monkey.decorators import record_exception, iter_account_region
from security_monkey.watcher import Watcher
from security_monkey.watcher import ChangeItem
from security_monkey import app


class EC2Instance(Watcher):
    index = 'ec2instance'
    i_am_singular = 'EC2 Instance'
    i_am_plural = 'EC2 Instances'

    def __init__(self, accounts=None, debug=False):
        super(EC2Instance, self).__init__(accounts=accounts, debug=debug)

    @record_exception()
    def describe_instances(self, **kwargs):
        from security_monkey.common.sts_connect import connect
        ec2 = connect(kwargs['account_name'], 'boto3.ec2.client', region=kwargs['region'],
                      assumed_role=kwargs['assumed_role'])

        response = self.wrap_aws_rate_limited_call(
            ec2.describe_instances
        )
        reservations = response.get('Reservations')
        return reservations

    def slurp(self):
        """
        :returns: item_list - list of EC2 instances in use by account
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
            reservations = self.describe_instances(**kwargs)

            if reservations:
                for reservation in reservations:
                    instances = reservation.get('Instances')
                    for instance in instances:
                        name = None
                        if instance.get('Tags') is not None:
                            for tag in instance.get('Tags'):
                                if tag['Key'] == 'Name':
                                    name = tag['Value']
                                    break

                        instance_id = instance['InstanceId']
                        if name is None:
                            name = instance_id

                        if self.check_ignore_list(name):
                            continue

                        config = {
                            'name': name,
                            'instance_id': instance_id,
                            'image_id': instance.get('ImageId'),
                            'state': instance.get('State'),
                            'private_dns_name': instance.get('PrivateDnsName'),
                            'public_dns_name': instance.get('PublicDnsName'),
                            'instance_type': instance.get('InstanceType'),
                            'launch_time': str(instance.get('LaunchTime')),
                            'placement': instance.get('placement'),
                            'subnet_id': instance.get('SubnetId'),
                            'vpc_id': instance.get('VpcId'),
                            'private_ip_address': instance.get('PrivateIpAddress'),
                            'public_ip_address': instance.get('PublicIpAddress'),
                            'security_groups': instance.get('SecurityGroups'),
                            'tags': instance.get('Tags'),
                        }

                        unique_name = name + '(' + instance_id + ')'

                        item = EC2InstanceItem(region=kwargs['region'],
                                               account=kwargs['account_name'],
                                               name=unique_name, config=dict(config), source_watcher=self)

                        item_list.append(item)

            return item_list, exception_map
        return slurp_items()


class EC2InstanceItem(ChangeItem):

    def __init__(self, region=None, account=None, name=None, config=None, source_watcher=None):
        super(EC2InstanceItem, self).__init__(
            index=EC2Instance.index,
            region=region,
            account=account,
            name=name,
            new_config=config if config else {},
            source_watcher=source_watcher)
