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
.. module: security_monkey.watchers.vpc
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
import json


def deep_dict(obj):
    """
    Serialize the Json, and then read it back as a dict.
    This casts the object to a dict, but does it recursively.

    You can cast an object to a dict with dict(), but that does not
    also convert sub-objects.
    :param obj: a datatructure likely containing Boto objects.
    :return: a dict where all branches or leaf nodes are either a
    python dict, list, or a primative such as int, boolean, basestr, or Nonetype
    """
    return json.loads(
        json.dumps(obj)
    )


class VPC(Watcher):
    index = 'vpc'
    i_am_singular = 'VPC'
    i_am_plural = 'VPCs'

    def __init__(self, accounts=None, debug=False):
        super(VPC, self).__init__(accounts=accounts, debug=debug)

    def slurp(self):
        """
        :returns: item_list - list of VPCs.
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
                    all_vpcs = self.wrap_aws_rate_limited_call(
                        conn.get_all_vpcs
                    )

                    all_dhcp_options = self.wrap_aws_rate_limited_call(
                        conn.get_all_dhcp_options
                    )

                    all_internet_gateways = self.wrap_aws_rate_limited_call(
                        conn.get_all_internet_gateways
                    )
                except Exception as e:
                    if region.name not in TROUBLE_REGIONS:
                        exc = BotoConnectionIssue(str(e), 'vpc', account, region.name)
                        self.slurp_exception((self.index, account, region.name), exc, exception_map)
                    continue
                app.logger.debug("Found {} {}".format(len(all_vpcs), self.i_am_plural))

                dhcp_options = {dhcp_option.id: dhcp_option.options for dhcp_option in all_dhcp_options}
                internet_gateways = {}
                for internet_gateway in all_internet_gateways:
                    for attachment in internet_gateway.attachments:
                        internet_gateways[attachment.vpc_id] = {
                            "id": internet_gateway.id,
                            "state": attachment.state
                        }

                for vpc in all_vpcs:

                    vpc_name = vpc.tags.get(u'Name', None)
                    vpc_name = "{0} ({1})".format(vpc_name, vpc.id)
                    if self.check_ignore_list(vpc_name):
                        continue

                    dhcp_options.get(vpc.dhcp_options_id, {}).update(
                        {"id": vpc.dhcp_options_id}
                    )

                    config = {
                        "name": vpc.tags.get(u'Name', None),
                        "id": vpc.id,
                        "cidr_block": vpc.cidr_block,
                        "instance_tenancy": vpc.instance_tenancy,
                        "is_default": vpc.is_default,
                        "state": vpc.state,
                        "tags": dict(vpc.tags),
                        "classic_link_enabled": vpc.classic_link_enabled,
                        "dhcp_options": deep_dict(dhcp_options.get(vpc.dhcp_options_id, {})),
                        "internet_gateway": internet_gateways.get(vpc.id, None)
                    }

                    item = VPCItem(region=region.name, account=account, name=vpc_name, config=config)
                    item_list.append(item)

        return item_list, exception_map


class VPCItem(ChangeItem):
    def __init__(self, region=None, account=None, name=None, config={}):
        super(VPCItem, self).__init__(
            index=VPC.index,
            region=region,
            account=account,
            name=name,
            new_config=config)
