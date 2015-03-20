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

from security_monkey.watcher import Watcher
from security_monkey.watcher import ChangeItem
from security_monkey.constants import TROUBLE_REGIONS
from security_monkey.exceptions import BotoConnectionIssue
from security_monkey import app

from boto.vpc import regions


class RouteTable(Watcher):
    index = 'routetable'
    i_am_singular = 'Route Table'
    i_am_plural = 'Route Tables'

    def __init__(self, accounts=None, debug=False):
        super(RouteTable, self).__init__(accounts=accounts, debug=debug)

    def slurp(self):
        """
        :returns: item_list - list of route tables.
        :returns: exception_map - A dict where the keys are a tuple containing the
            location of the exception and the value is the actual exception

        """
        self.prep_for_slurp()

        item_list = []
        exception_map = {}
        from security_monkey.common.sts_connect import connect
        for account in self.accounts:
            for region in regions():
                app.logger.debug("Checking {}/{}/{}".format(self.index, account, region.name))
                try:
                    conn = connect(account, 'vpc', region=region)
                    all_route_tables = self.wrap_aws_rate_limited_call(
                        conn.get_all_route_tables
                    )
                except Exception as e:
                    if region.name not in TROUBLE_REGIONS:
                        exc = BotoConnectionIssue(str(e), self.index, account, region.name)
                        self.slurp_exception((self.index, account, region.name), exc, exception_map)
                    continue
                app.logger.debug("Found {} {}".format(len(all_route_tables), self.i_am_plural))

                for route_table in all_route_tables:

                    subnet_name = route_table.tags.get(u'Name', None)
                    if subnet_name:
                        subnet_name = "{0} ({1})".format(subnet_name, route_table.id)
                    else:
                        subnet_name = route_table.id

                    if self.check_ignore_list(subnet_name):
                        continue

                    routes = []
                    for boto_route in route_table.routes:
                        routes.append({
                            "destination_cidr_block": boto_route.destination_cidr_block,
                            "gateway_id": boto_route.gateway_id,
                            "instance_id": boto_route.instance_id,
                            "interface_id": boto_route.interface_id,
                            "state": boto_route.state,
                            "vpc_peering_connection_id": boto_route.vpc_peering_connection_id
                        })

                    associations = []
                    for boto_association in route_table.associations:
                        associations.append({
                            "id": boto_association.id,
                            "main": boto_association.main,
                            "subnet_id": boto_association.subnet_id
                        })

                    config = {
                        "name": route_table.tags.get(u'Name', None),
                        "id": route_table.id,
                        "routes": routes,
                        "tags": dict(route_table.tags),
                        "vpc_id": route_table.vpc_id,
                        "associations": associations
                    }

                    item = RouteTableItem(region=region.name, account=account, name=subnet_name, config=config)
                    item_list.append(item)

        return item_list, exception_map


class RouteTableItem(ChangeItem):
    def __init__(self, region=None, account=None, name=None, config={}):
        super(RouteTableItem, self).__init__(
            index=RouteTable.index,
            region=region,
            account=account,
            name=name,
            new_config=config)
