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
.. module: security_monkey.auditors.security_group
    :platform: Unix

.. version:: $$VERSION$$
.. moduleauthor:: Patrick Kelley <pkelley@netflix.com> @monkeysecurity

"""

from security_monkey.auditor import Auditor
from security_monkey.watchers.security_group import SecurityGroup


class SecurityGroupAuditor(Auditor):
    index = SecurityGroup.index
    i_am_singular = SecurityGroup.i_am_singular
    i_am_plural = SecurityGroup.i_am_plural
    network_whitelist = []

    def __init__(self, accounts=None, debug=False):
        super(SecurityGroupAuditor, self).__init__(accounts=accounts, debug=debug)

    def __port_for_rule__(self, rule):
        """
        Looks at the from_port and to_port and returns a sane representation
        """
        if rule['from_port'] == rule['to_port']:
            return "{} {}".format(rule['ip_protocol'], rule['from_port'])

        return "{} {}-{}".format(rule['ip_protocol'], rule['from_port'], rule['to_port'])

    def check_securitygroup_rule_count(self, sg_item):
        """
        alert if SG has more than 50 rules
        """
        tag = "Security Group contains 50 or more rules"
        severity = 1
        rules = sg_item.config.get('rules', [])
        if len(rules) >= 50:
            self.add_issue(severity, tag, sg_item)

    def check_securitygroup_large_subnet(self, sg_item):
        """
        Make sure the SG does not contain large networks.
        """
        tag = "Security Group network larger than /24"
        severity = 3
        for rule in sg_item.config.get("rules", []):
            cidr = rule.get("cidr_ip", None)
            if cidr and not cidr in self.network_whitelist:
                if '/' in cidr and not cidr == "0.0.0.0/0" and not cidr == "10.0.0.0/8":
                    mask = int(cidr.split('/')[1])
                    if mask < 24 and mask > 0:
                        notes = "{} on {}".format(cidr, self.__port_for_rule__(rule))
                        self.add_issue(severity, tag, sg_item, notes=notes)

    def check_securitygroup_zero_subnet(self, sg_item):
        """
        Make sure the SG does not contain a cidr with a subnet length of zero.
        """
        tag = "Security Group subnet mask is /0"
        severity = 10
        for rule in sg_item.config.get("rules", []):
            cidr = rule.get("cidr_ip", None)
            if cidr and '/' in cidr and not cidr == "0.0.0.0/0" and not cidr == "10.0.0.0/8":
                mask = int(cidr.split('/')[1])
                if mask == 0:
                    notes = "{} on {}".format(cidr, self.__port_for_rule__(rule))
                    self.add_issue(severity, tag, sg_item, notes=notes)

    def check_securitygroup_any(self, sg_item):
        """
        Make sure the SG does not contain 0.0.0.0/0
        """
        tag = "Security Group contains 0.0.0.0/0"
        severity = 5
        for rule in sg_item.config.get("rules", []):
            cidr = rule.get("cidr_ip")
            if "0.0.0.0/0" == cidr:
                notes = "{} on {}".format(cidr, self.__port_for_rule__(rule))
                self.add_issue(severity, tag, sg_item, notes=notes)

    def check_securitygroup_10net(self, sg_item):
        """
        Make sure the SG does not contain 10.0.0.0/8
        """
        tag = "Security Group contains 10.0.0.0/8"
        severity = 5

        if sg_item.config.get("vpc_id", None):
            return

        for rule in sg_item.config.get("rules", []):
            cidr = rule.get("cidr_ip")
            if "10.0.0.0/8" == cidr:
                notes = "{} on {}".format(cidr, self.__port_for_rule__(rule))
                self.add_issue(severity, tag, sg_item, notes=notes)
