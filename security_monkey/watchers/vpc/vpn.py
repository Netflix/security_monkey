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
.. module: security_monkey.watchers.vpc.vpn
    :platform: Unix

.. version:: $$VERSION$$
.. moduleauthor:: Alex Cline <alex.cline@gmail.com> @alex.cline

"""
from security_monkey.decorators import record_exception, iter_account_region
from security_monkey.watcher import Watcher
from security_monkey.watcher import ChangeItem
from security_monkey import app

from dateutil.tz import tzutc

class VPN(Watcher):
    index = 'vpn'
    i_am_singular = 'VPN Connection'
    i_am_plural = 'VPN Connections'

    def __init__(self, accounts=None, debug=False):
        super(VPN, self).__init__(accounts=accounts, debug=debug)
        self.ephemeral_paths = ['tunnels$*$last_status_change']

    @record_exception()
    def describe_vpns(self, **kwargs):
        from security_monkey.common.sts_connect import connect
        conn = connect(kwargs['account_name'], 'boto3.ec2.client',
                       region=kwargs['region'], assumed_role=kwargs['assumed_role'])

        response = self.wrap_aws_rate_limited_call(conn.describe_vpn_connections)
        all_vpns = response.get('VpnConnections', [])
        return all_vpns

    def slurp(self):
        """
        :returns: item_list - list of vpn connections.
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

            all_vpns = self.describe_vpns(**kwargs)

            if all_vpns:
                app.logger.debug("Found {} {}".format(len(all_vpns), self.i_am_plural))

                for vpn in all_vpns:
                    tags = vpn.get('Tags', {})
                    joined_tags = {}
                    for tag in tags:
                        if tag.get('Key') and tag.get('Value'):
                            joined_tags[tag['Key']] = tag['Value']
                    vpn_name = joined_tags.get('Name')
                    vpn_id   = vpn.get('VpnConnectionId')

                    if vpn_name:
                        vpn_name = "{0} ({1})".format(vpn_name, vpn_id)
                    else:
                        vpn_name = vpn_id

                    if self.check_ignore_list(vpn_name):
                        continue

                    tunnels = []
                    for tunnel in vpn.get('VgwTelemetry'):
                        tunnels.append({
                            "status": tunnel.get('Status'),
                            "accepted_route_count": tunnel.get('AcceptedRouteCount'),
                            "outside_ip_address": tunnel.get('OutsideIpAddress'),
                            "last_status_change": tunnel.get('LastStatusChange').astimezone(tzutc()).isoformat(),
                            "status_message": tunnel.get('StatusMessage')
                        })

                    arn = 'arn:aws:ec2:{region}:{account_number}:vpn-connection/{vpn_id}'.format(
                        region=kwargs['region'],
                        account_number=kwargs['account_number'],
                        vpn_id=vpn_id)

                    config = {
                        "name": joined_tags.get('Name'),
                        "arn": arn,
                        "id": vpn_id,
                        "tags": joined_tags,
                        "type": vpn.get('Type'),
                        "state": vpn.get('State'),
                        "tunnels": tunnels,
                        "vpn_gateway_id": vpn.get('VpnGatewayId'),
                        "customer_gateway_id": vpn.get('CustomerGatewayId')
                    }

                    item = VPNItem(region=kwargs['region'],
                                          account=kwargs['account_name'],
                                          name=vpn_name, arn=arn, config=config)

                    item_list.append(item)

            return item_list, exception_map
        return slurp_items()

class VPNItem(ChangeItem):
    def __init__(self, region=None, account=None, name=None, arn=None, config={}):
        super(VPNItem, self).__init__(
            index=VPN.index,
            region=region,
            account=account,
            name=name,
            arn=arn,
            new_config=config)
