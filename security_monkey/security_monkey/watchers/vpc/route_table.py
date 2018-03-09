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


class RouteTable(Watcher):
    index = 'routetable'
    i_am_singular = 'Route Table'
    i_am_plural = 'Route Tables'

    def __init__(self, accounts=None, debug=False):
        super(RouteTable, self).__init__(accounts=accounts, debug=debug)

    @record_exception()
    def describe_route_tables(self, **kwargs):
        from security_monkey.common.sts_connect import connect
        conn = connect(kwargs['account_name'], 'boto3.ec2.client',
                       region=kwargs['region'], assumed_role=kwargs['assumed_role'])

        response = self.wrap_aws_rate_limited_call(conn.describe_route_tables)
        all_route_tables = response.get('RouteTables', [])
        return all_route_tables

    def slurp(self):
        """
        :returns: item_list - list of route tables.
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
                             kwargs['account_name'],
                             kwargs['region']))

            all_route_tables = self.describe_route_tables(**kwargs)

            if all_route_tables:
                app.logger.debug("Found {} {}".format(len(all_route_tables), self.i_am_plural))

                for route_table in all_route_tables:
                    tags = route_table.get('Tags', {})
                    joined_tags = {}
                    for tag in tags:
                        if tag.get('Key') and tag.get('Value'):
                            joined_tags[tag['Key']] = tag['Value']
                    subnet_name = joined_tags.get('Name')

                    if subnet_name:
                        subnet_name = "{0} ({1})".format(subnet_name, route_table.get('RouteTableId'))
                    else:
                        subnet_name = route_table.get('RouteTableId')

                    if self.check_ignore_list(subnet_name):
                        continue

                    routes = []
                    for boto_route in route_table.get('Routes'):
                        routes.append({
                            "destination_cidr_block": boto_route.get('DestinationCidrBlock'),
                            "gateway_id": boto_route.get('GatewayId'),
                            "instance_id": boto_route.get('InstanceId'),
                            "interface_id": boto_route.get('NetworkInterfaceId'),
                            'nat_gateway_id': boto_route.get('NatGatewayId'),
                            "state": boto_route.get('State'),
                            "vpc_peering_connection_id": boto_route.get('VpcPeeringConnectionId')
                        })

                    associations = []
                    for boto_association in route_table.get('Associations'):
                        associations.append({
                            "id": boto_association.get('RouteTableAssociationId'),
                            "main": boto_association.get('Main', False),
                            "subnet_id": boto_association.get('SubnetId')
                        })

                    arn = ARN_PREFIX + ':ec2:{region}:{account_number}:route-table/{route_table_id}'.format(
                        region=kwargs['region'],
                        account_number=kwargs['account_number'],
                        route_table_id=route_table.get('RouteTableId'))

                    config = {
                        "name": joined_tags.get('Name'),
                        "arn": arn,
                        "id": route_table.get('RouteTableId'),
                        "routes": routes,
                        "tags": joined_tags,
                        "vpc_id": route_table.get('VpcId'),
                        "associations": associations
                    }

                    item = RouteTableItem(region=kwargs['region'],
                                          account=kwargs['account_name'],
                                          name=subnet_name, arn=arn, config=config, source_watcher=self)

                    item_list.append(item)

            return item_list, exception_map
        return slurp_items()


class RouteTableItem(ChangeItem):
    def __init__(self, region=None, account=None, name=None, arn=None, config=None, source_watcher=None):
        super(RouteTableItem, self).__init__(
            index=RouteTable.index,
            region=region,
            account=account,
            name=name,
            arn=arn,
            new_config=config if config else {},
            source_watcher=source_watcher)
