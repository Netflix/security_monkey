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
.. module: security_monkey.watchers.direct_connect.virtual_gateway
    :platform: Unix

.. version:: $$VERSION$$
.. moduleauthor:: Bridgewater OSS <opensource@bwater.com>


"""
from security_monkey.watcher import Watcher
from security_monkey.watcher import ChangeItem
from security_monkey.constants import TROUBLE_REGIONS
from security_monkey.exceptions import BotoConnectionIssue
from security_monkey import app
from boto.directconnect import regions


class VirtualGateway(Watcher):
    index = 'virtual_gateway'
    i_am_singular = 'Virtual Gateway'
    i_am_plural = 'Virtual Gateways'

    def __init__(self, accounts=None, debug=False):
        super(VirtualGateway, self).__init__(accounts=accounts, debug=debug)

    def slurp(self):
        """
        :returns: item_list - list of virtual gateways
        :returns: exception_map - A dict where the keys are a tuple containing the
            location of the exception and the value is the actual exception

        """
        self.prep_for_slurp()
        from security_monkey.common.sts_connect import connect
        item_list = []
        exception_map = {}
        for account in self.accounts:
            for region in regions():
                app.logger.debug(
                    "Checking {}/{}/{}".format(self.index, account, region.name))
                try:
                    dc = connect(account, 'boto3.ec2.client', region=region)
                    response = self.wrap_aws_rate_limited_call(
                        dc.describe_vpn_gateways
                    )
                    gateways = response.get('VpnGateways')
                except Exception as e:
                    if region.name not in TROUBLE_REGIONS:
                        exc = BotoConnectionIssue(
                            str(e), self.index, account, region.name)
                        self.slurp_exception(
                            (self.index, account, region.name), exc, exception_map)
                    continue
                app.logger.debug("Found {} {}.".format(
                    len(gateways), self.i_am_plural))
                for gateway in gateways:

                    name = gateway['VpnGatewayId']
                    if self.check_ignore_list(name):
                        continue

                    config = {
                        'name': name,
                        'state': gateway.get('State'),
                        'type': gateway.get('Type'),
                        'vpcAttachments': gateway.get('VpcAttachments'),
                        'virtual_gateway_state': gateway.get('VirtualGatewayState')
                    }

                    item = VirtualGatewayItem(
                        region=region.name, account=account, name=name, config=dict(config), source_watcher=self)
                    item_list.append(item)

        return item_list, exception_map


class VirtualGatewayItem(ChangeItem):

    def __init__(self, region=None, account=None, name=None, config=None, source_watcher=None):
        super(VirtualGatewayItem, self).__init__(
            index=VirtualGateway.index,
            region=region,
            account=account,
            name=name,
            new_config=config if config else {},
            source_watcher=source_watcher)
