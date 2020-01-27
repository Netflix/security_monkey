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
.. module: security_monkey.watchers.vpc.endpoint
    :platform: Unix

.. version:: $$VERSION$$
.. moduleauthor:: Bridgewater OSS <opensource@bwater.com>


"""
from security_monkey.watcher import Watcher
from security_monkey.watcher import ChangeItem
from security_monkey.constants import TROUBLE_REGIONS
from security_monkey.exceptions import BotoConnectionIssue
from security_monkey import app

from boto.vpc import regions


class Endpoint(Watcher):
    index = 'endpoint'
    i_am_singular = 'Endpoint'
    i_am_plural = 'Endpoints'

    def __init__(self, accounts=None, debug=False):
        super(Endpoint, self).__init__(accounts=accounts, debug=debug)

    def slurp(self):
        """
        :returns: item_list - list of endpoints.
        :returns: exception_map - A dict where the keys are a tuple containing the
            location of the exception and the value is the actual exception

        """
        self.prep_for_slurp()

        item_list = []
        exception_map = {}
        from security_monkey.common.sts_connect import connect
        for account in self.accounts:
            for region in regions():
                app.logger.debug(
                    "Checking {}/{}/{}".format(self.index, account, region.name))
                try:
                    conn = connect(account, 'boto3.ec2.client', region=region)
                    all_vpc_endpoints_resp = self.wrap_aws_rate_limited_call(
                        conn.describe_vpc_endpoints
                    )

                    all_vpc_endpoints = all_vpc_endpoints_resp.get(
                        'VpcEndpoints', [])
                except Exception as e:
                    if region.name not in TROUBLE_REGIONS:
                        exc = BotoConnectionIssue(
                            str(e), self.index, account, region.name)
                        self.slurp_exception(
                            (self.index, account, region.name), exc, exception_map)
                    continue
                app.logger.debug("Found {} {}".format(
                    len(all_vpc_endpoints), self.i_am_plural))

                for endpoint in all_vpc_endpoints:

                    endpoint_name = endpoint.get('VpcEndpointId')

                    if self.check_ignore_list(endpoint_name):
                        continue

                    service = endpoint.get('ServiceName', '').split('.')[-1]

                    config = {
                        "id": endpoint.get('VpcEndpointId'),
                        "policy_document": endpoint.get('PolicyDocument', {}),
                        "service_name": endpoint.get('ServiceName'),
                        "service": service,
                        "route_table_ids": endpoint.get('RouteTableIds', []),
                        "creation_time_stamp": str(endpoint.get('CreationTimestamp')),
                        "state": endpoint.get('State'),
                        "vpc_id": endpoint.get('VpcId'),
                    }

                    item = EndpointItem(
                        region=region.name, account=account, name=endpoint_name, config=config, source_watcher=self)
                    item_list.append(item)

        return item_list, exception_map


class EndpointItem(ChangeItem):

    def __init__(self, region=None, account=None, name=None, config=None, source_watcher=None):
        super(EndpointItem, self).__init__(
            index=Endpoint.index,
            region=region,
            account=account,
            name=name,
            new_config=config if config else {},
            source_watcher=source_watcher)
