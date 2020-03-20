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
.. module: security_monkey.watchers.peering
    :platform: Unix

.. version:: $$VERSION$$
.. moduleauthor:: Bridgewater OSS <opensource@bwater.com>


"""
from security_monkey.decorators import record_exception, iter_account_region
from security_monkey.watcher import Watcher
from security_monkey.watcher import ChangeItem
from security_monkey import app


class Peering(Watcher):
    index = 'peering'
    i_am_singular = 'VPC peering connection'
    i_am_plural = 'VPC peering connections'

    def __init__(self, accounts=None, debug=False):
        super(Peering, self).__init__(accounts=accounts, debug=debug)

    @record_exception()
    def describe_vpc_peering_connections(self, **kwargs):
        from security_monkey.common.sts_connect import connect
        conn = connect(kwargs['account_name'], 'boto3.ec2.client', region=kwargs['region'],
                       assumed_role=kwargs['assumed_role'])

        peering_info = self.wrap_aws_rate_limited_call(
            conn.describe_vpc_peering_connections)
        return peering_info

    def slurp(self):
        """
        :returns: item_list - list of vpc peerings.
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
            peering_info = self.describe_vpc_peering_connections(**kwargs)

            if peering_info:
                all_peerings = peering_info.get('VpcPeeringConnections', [])
                app.logger.debug("Found {} {}".format(
                    len(all_peerings), self.i_am_plural))

                for peering in all_peerings:
                    connection_id = peering['VpcPeeringConnectionId']
                    tags = peering.get('Tags')
                    peering_name = None

                    if tags:
                        peering_name = tags[0].get('Value', None)

                    if not (peering_name is None):
                        peering_name = "{0} ({1})".format(
                            peering_name.encode('utf-8', 'ignore'), connection_id)
                    else:
                        peering_name = connection_id

                    if self.check_ignore_list(peering_name):
                        continue

                    config = {
                        "name": peering_name,
                        "status": peering['Status'],
                        "accepter_vpc_info": peering['AccepterVpcInfo'],
                        "expiration_time": str(peering.get('ExpirationTime')),
                        "requester_vpc_info": peering['RequesterVpcInfo'],
                        "vpc_peering_connection_id": peering['VpcPeeringConnectionId']
                    }

                    item = PeeringItem(region=kwargs['region'],
                                       account=kwargs['account_name'],
                                       name=peering_name, config=config, source_watcher=self)

                    item_list.append(item)

            return item_list, exception_map
        return slurp_items()


class PeeringItem(ChangeItem):

    def __init__(self, region=None, account=None, name=None, config=None, source_watcher=None):
        super(PeeringItem, self).__init__(
            index=Peering.index,
            region=region,
            account=account,
            name=name,
            new_config=config if config else {},
            source_watcher=source_watcher)
