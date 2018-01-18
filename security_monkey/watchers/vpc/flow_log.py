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
.. module: security_monkey.watchers.vpc.flow_log
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


class FlowLog(Watcher):
    index = 'flowlog'
    i_am_singular = 'Flow Log'
    i_am_plural = 'Flow Logs'

    def __init__(self, accounts=None, debug=False):
        super(FlowLog, self).__init__(accounts=accounts, debug=debug)

    def slurp(self):
        """
        :returns: item_list - list of Flow Logs in use by account
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

                response_items = []
                try:
                    conn = connect(account, 'boto3.ec2.client', region=region)

                    next_token = None
                    while True:
                        if next_token:
                            response = self.wrap_aws_rate_limited_call(
                                conn.describe_flow_logs,
                                NextToken=next_token
                            )
                        else:
                            response = self.wrap_aws_rate_limited_call(
                                conn.describe_flow_logs
                            )

                        response_items.extend(response.get('FlowLogs'))

                        if response.get('NextToken'):
                            next_token = response.get('NextToken')
                        else:
                            break

                except Exception as e:
                    if region.name not in TROUBLE_REGIONS:
                        exc = BotoConnectionIssue(
                            str(e), self.index, account, region.name)
                        self.slurp_exception(
                            (self.index, account, region.name), exc, exception_map)
                    continue

                app.logger.debug("Found {} {}".format(
                    len(response_items), self.i_am_plural))

                for response_item in response_items:

                    name = "{} ({})".format(response_item.get(
                        'LogGroupName'), response_item.get('FlowLogId'))

                    if self.check_ignore_list(name):
                        continue

                    config = {
                        'creation_time': str(response_item.get('CreationTime')),
                        'deliver_logs_permission_arn': response_item.get('DeliverLogsPermissionArn'),
                        'flow_log_id': response_item.get('FlowLogId'),
                        'flow_log_status': response_item.get('FlowLogStatus'),
                        'log_group_name': response_item.get('LogGroupName'),
                        'resource_id': response_item.get('ResourceId'),
                        'traffic_type': response_item.get('TrafficType')
                    }

                    item = FlowLogItem(
                        region=region.name, account=account, name=name, config=dict(config), source_watcher=self)
                    item_list.append(item)

        return item_list, exception_map


class FlowLogItem(ChangeItem):

    def __init__(self, region=None, account=None, name=None, config=None, source_watcher=None):
        super(FlowLogItem, self).__init__(
            index=FlowLog.index,
            region=region,
            account=account,
            name=name,
            new_config=config if config else {},
            source_watcher=source_watcher)
