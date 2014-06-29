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
.. module: security_monkey.auditors.rds_security_group
    :platform: Unix

.. version:: $$VERSION$$
.. moduleauthor:: Patrick Kelley <pkelley@netflix.com> @monkeysecurity

"""
from security_monkey.auditor import Auditor
from security_monkey.watchers.rds_security_group import RDSSecurityGroup


class RDSSecurityGroupAuditor(Auditor):
    index = RDSSecurityGroup.index
    i_am_singular = RDSSecurityGroup.i_am_singular
    i_am_plural = RDSSecurityGroup.i_am_plural

    def __init__(self, accounts=None, debug=False):
        super(RDSSecurityGroupAuditor, self).__init__(accounts=accounts, debug=debug)

    def check_securitygroup_zero_subnet(self, sg_item):
        """
        Make sure the RDS SG does not contain a cidr with a subnet length of zero.
        """
        tag = "RDS Security Group subnet mask is /0"
        severity = 10
        for ipr in sg_item.config.get("ip_ranges", []):
            cidr = ipr.get("cidr_ip", None)
            if cidr and '/' in cidr and not cidr == "0.0.0.0/0" and not cidr == "10.0.0.0/8":
                mask = int(cidr.split('/')[1])
                if mask == 0:
                    self.add_issue(severity, tag, sg_item, notes=cidr)

    def check_securitygroup_any(self, sg_item):
        """
        Make sure the RDS SG does not contain 0.0.0.0/0
        """
        tag = "RDS Security Group contains 0.0.0.0/0"
        severity = 5
        for ipr in sg_item.config.get("ip_ranges", []):
            cidr = ipr.get("cidr_ip")
            if "0.0.0.0/0" == cidr:
                self.add_issue(severity, tag, sg_item, notes=cidr)
                return

    def check_securitygroup_10net(self, sg_item):
        """
        Make sure the RDS SG does not contain 10.0.0.0/8
        """
        tag = "RDS Security Group contains 10.0.0.0/8"
        severity = 5

        for ipr in sg_item.config.get("ip_ranges", []):
            cidr = ipr.get("cidr_ip")
            if "10.0.0.0/8" == cidr:
                self.add_issue(severity, tag, sg_item, notes=cidr)
                return
