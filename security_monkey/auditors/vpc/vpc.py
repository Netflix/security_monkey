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
from security_monkey import app
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
        self.account_mapping = {}

    def check_flow_logs_enabled(self, vpc_item):
        """
        alert when flow logs are not enabled for VPC
        """
        if not self.account_mapping.get(vpc_item.account):
            flow_log_items = self.get_watcher_support_items(FlowLog.index, vpc_item.account)

            self.account_mapping[vpc_item.account] = {fl.config["flow_log_id"]: fl.config["flow_log_status"]
                                                      for fl in flow_log_items}

        tag = "Flow Logs not enabled for VPC"
        severity = 5

        if not vpc_item.config.get("FlowLogs"):
            self.add_issue(severity, tag, vpc_item)

        else:
            flow_logs_disabled_count = 0

            for log in vpc_item.config["FlowLogs"]:
                if not self.account_mapping[vpc_item.account].get(log):
                    # This may not have been seen yet, so skip.
                    app.logger.debug("[/] Can't find flow log entry with ID: {}. It may not have been seen yet, "
                                     "so skipping...".format(log))
                    continue

                if self.account_mapping[vpc_item.account][log] != "ACTIVE":
                    flow_logs_disabled_count += 1

            if flow_logs_disabled_count:
                self.add_issue(severity, tag, vpc_item)
