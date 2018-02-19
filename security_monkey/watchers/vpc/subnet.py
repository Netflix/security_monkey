#     Copyright 2014 Netflix, Inc.
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
.. module: security_monkey.watchers.subnet
    :platform: Unix

.. version:: $$VERSION$$
.. moduleauthor:: Patrick Kelley <pkelley@netflix.com> @monkeysecurity

"""
from security_monkey.decorators import record_exception, iter_account_region
from security_monkey.watcher import Watcher
from security_monkey.watcher import ChangeItem
from security_monkey import app, ARN_PREFIX


class Subnet(Watcher):
    index = 'subnet'
    i_am_singular = 'Subnet'
    i_am_plural = 'Subnets'

    def __init__(self, accounts=None, debug=False):
        super(Subnet, self).__init__(accounts=accounts, debug=debug)

    @record_exception()
    def get_all_subnets(self, **kwargs):
        from security_monkey.common.sts_connect import connect
        conn = connect(kwargs['account_name'], 'boto3.ec2.client', region=kwargs['region'],
                       assumed_role=kwargs['assumed_role'])

        all_subnets = self.wrap_aws_rate_limited_call(conn.describe_subnets)
        return all_subnets.get('Subnets')

    def slurp(self):
        """
        :returns: item_list - list of subnets.
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
            all_subnets = self.get_all_subnets(**kwargs)

            if all_subnets:
                app.logger.debug("Found {} {}".format(len(all_subnets), self.i_am_plural))

                for subnet in all_subnets:

                    subnet_name = None
                    for tag in subnet.get('Tags', []):
                        if tag.get('Key') == 'Name':
                            subnet_name = tag.get('Value')
                    subnet_id = subnet.get('SubnetId')
                    if subnet_name:
                        subnet_name = "{0} ({1})".format(subnet_name, subnet_id)
                    else:
                        subnet_name = subnet_id

                    if self.check_ignore_list(subnet_name):
                        continue

                    arn = ARN_PREFIX + ':ec2:{region}:{account_number}:subnet/{subnet_id}'.format(
                        region=kwargs["region"],
                        account_number=kwargs["account_number"],
                        subnet_id=subnet_id)

                    config = {
                        "name": subnet_name,
                        "arn": arn,
                        "id": subnet_id,
                        "cidr_block": subnet.get('CidrBlock'),
                        "availability_zone": subnet.get('AvailabilityZone'),
                        # TODO:
                        # available_ip_address_count is likely to change often
                        # and should be in the upcoming ephemeral section.
                        # "available_ip_address_count": subnet.available_ip_address_count,
                        "defaultForAz": subnet.get('DefaultForAz'),
                        "mapPublicIpOnLaunch": subnet.get('MapPublicIpOnLaunch'),
                        "state": subnet.get('State'),
                        "tags": subnet.get('Tags'),
                        "vpc_id": subnet.get('VpcId')
                    }

                    item = SubnetItem(region=kwargs['region'],
                                      account=kwargs['account_name'],
                                      name=subnet_name, arn=arn, config=config)

                    item_list.append(item)

            return item_list, exception_map
        return slurp_items()


class SubnetItem(ChangeItem):
    def __init__(self, region=None, account=None, name=None, arn=None, config=None, source_watcher=None):
        super(SubnetItem, self).__init__(
            index=Subnet.index,
            region=region,
            account=account,
            name=name,
            arn=arn,
            new_config=config if config else {},
            source_watcher=source_watcher)
