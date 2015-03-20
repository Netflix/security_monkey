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


class Subnet(Watcher):
    index = 'subnet'
    i_am_singular = 'Subnet'
    i_am_plural = 'Subnets'

    def __init__(self, accounts=None, debug=False):
        super(Subnet, self).__init__(accounts=accounts, debug=debug)

    def slurp(self):
        """
        :returns: item_list - list of subnets.
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
                    all_subnets = self.wrap_aws_rate_limited_call(
                        conn.get_all_subnets
                    )
                except Exception as e:
                    if region.name not in TROUBLE_REGIONS:
                        exc = BotoConnectionIssue(str(e), self.index, account, region.name)
                        self.slurp_exception((self.index, account, region.name), exc, exception_map)
                    continue
                app.logger.debug("Found {} {}".format(len(all_subnets), self.i_am_plural))

                for subnet in all_subnets:

                    subnet_name = subnet.tags.get(u'Name', None)
                    if subnet_name:
                        subnet_name = "{0} ({1})".format(subnet_name, subnet.id)
                    else:
                        subnet_name = subnet.id

                    if self.check_ignore_list(subnet_name):
                        continue

                    config = {
                        "name": subnet.tags.get(u'Name', None),
                        "id": subnet.id,
                        "cidr_block": subnet.cidr_block,
                        "availability_zone": subnet.availability_zone,
                        # TODO:
                        # available_ip_address_count is likely to change often
                        # and should be in the upcoming ephemeral section.
                        # "available_ip_address_count": subnet.available_ip_address_count,
                        "defaultForAz": subnet.defaultForAz,
                        "mapPublicIpOnLaunch": subnet.mapPublicIpOnLaunch,
                        "state": subnet.state,
                        "tags": dict(subnet.tags),
                        "vpc_id": subnet.vpc_id
                    }

                    item = SubnetItem(region=region.name, account=account, name=subnet_name, config=config)
                    item_list.append(item)

        return item_list, exception_map


class SubnetItem(ChangeItem):
    def __init__(self, region=None, account=None, name=None, config={}):
        super(SubnetItem, self).__init__(
            index=Subnet.index,
            region=region,
            account=account,
            name=name,
            new_config=config)
