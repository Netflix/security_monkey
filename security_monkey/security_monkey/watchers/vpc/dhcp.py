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
.. module: security_monkey.watchers.vpc.dhcp
    :platform: Unix

.. version:: $$VERSION$$
.. moduleauthor:: Bridgewater OSS <opensource@bwater.com>


"""
from security_monkey.decorators import record_exception, iter_account_region
from security_monkey.watcher import Watcher
from security_monkey.watcher import ChangeItem
from security_monkey import app


class DHCP(Watcher):
    index = 'dhcp'
    i_am_singular = 'DHCP Option Set'
    i_am_plural = 'DHCP Option Sets'

    def __init__(self, accounts=None, debug=False):
        super(DHCP, self).__init__(accounts=accounts, debug=debug)

    @record_exception()
    def describe_dhcp_options(self, **kwargs):
        from security_monkey.common.sts_connect import connect
        conn = connect(kwargs['account_name'], 'boto3.ec2.client', region=kwargs['region'],
                       assumed_role=kwargs['assumed_role'])

        dhcp_option_sets_resp = self.wrap_aws_rate_limited_call(
            conn.describe_dhcp_options)
        dhcp_option_sets = dhcp_option_sets_resp.get('DhcpOptions', [])
        return dhcp_option_sets

    def slurp(self):
        """
        :returns: item_list - list of dhcp option sets.
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
            dhcp_option_sets = self.describe_dhcp_options(**kwargs)

            if dhcp_option_sets:
                app.logger.debug("Found {} {}".format(
                    len(dhcp_option_sets), self.i_am_plural))

                for dhcpopt in dhcp_option_sets:

                    dhcpopt_id = dhcpopt.get('DhcpOptionsId')

                    if self.check_ignore_list(dhcpopt_id):
                        continue

                    dhcpopt_configurations = dhcpopt.get(
                        'DhcpConfigurations', [])

                    config = {'id': dhcpopt_id}

                    for option in dhcpopt_configurations:
                        key = option['Key']
                        values = option['Values']
                        if len(values) == 1:
                            config[key] = values[0]['Value']
                        else:
                            config[key] = []
                            for val in values:
                                config[key].append(val['Value'])

                    item = DHCPItem(region=kwargs['region'],
                                    account=kwargs['account_name'],
                                    name=dhcpopt_id, config=config, source_watcher=self)

                    item_list.append(item)

            return item_list, exception_map
        return slurp_items()


class DHCPItem(ChangeItem):

    def __init__(self, region=None, account=None, name=None, config=None, source_watcher=None):
        super(DHCPItem, self).__init__(
            index=DHCP.index,
            region=region,
            account=account,
            name=name,
            new_config=config if config else {},
            source_watcher=source_watcher)
