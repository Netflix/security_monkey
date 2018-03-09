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
.. module: security_monkey.auditors.vpc
    :platform: Unix

.. version:: $$VERSION$$
.. moduleauthor:: Bridgewater OSS <opensource@bwater.com>


"""
from security_monkey.auditor import Auditor
from security_monkey.watchers.vpc.vpc import VPC
from security_monkey.watchers.vpc.flow_log import FlowLog


class VPCAuditor(Auditor):
    index = VPC.index
    i_am_singular = VPC.i_am_singular
    i_am_plural = VPC.i_am_plural
    support_watcher_indexes = [FlowLog.index]

    def __init__(self, accounts=None, debug=False):
        super(VPCAuditor, self).__init__(accounts=accounts, debug=debug)

    def check_flow_logs_enabled(self, vpc_item):
        """
        alert when flow logs are not enabled for VPC
        """
        flow_log_items = self.get_watcher_support_items(
            FlowLog.index, vpc_item.account)
        vpc_id = vpc_item.config.get("id")

        tag = "Flow Logs not enabled for VPC"
        severity = 5

        flow_logs_enabled = False
        for flow_log in flow_log_items:
            if vpc_id == flow_log.config.get("resource_id"):
                flow_logs_enabled = True
                break

        if not flow_logs_enabled:
            self.add_issue(severity, tag, vpc_item)
