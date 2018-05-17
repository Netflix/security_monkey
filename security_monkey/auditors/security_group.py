# Copyright 2014 Netflix, Inc.
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

from security_monkey.auditor import Auditor, Entity
from security_monkey.watchers.security_group import SecurityGroup
from security_monkey.common.utils import check_rfc_1918
from security_monkey import app


def _check_empty_security_group(sg_item):
    if app.config.get('SECURITYGROUP_INSTANCE_DETAIL', None) in ['SUMMARY', 'FULL'] and \
            not sg_item.config.get("assigned_to", None):
        return 0
    return 1


class SecurityGroupAuditor(Auditor):
    index = SecurityGroup.index
    i_am_singular = SecurityGroup.i_am_singular
    i_am_plural = SecurityGroup.i_am_plural

    def __init__(self, accounts=None, debug=False):
        super(SecurityGroupAuditor, self).__init__(accounts=accounts, debug=debug)

    def _port_for_rule(self, rule):
        """
        Looks at the from_port and to_port and returns a sane representation.
        """
        phrase = '{direction}:{protocol}:{port}'
        direction = rule.get('rule_type')
        protocol = rule['ip_protocol']
        port_range = '{0}-{1}'.format(rule['from_port'], rule['to_port'])

        if protocol == '-1':
            protocol = 'all_protocols'
            port_range = 'all_ports'

        elif rule['from_port'] == rule['to_port']:
            port_range = str(rule['from_port'])

        return phrase.format(direction=direction, protocol=protocol, port=port_range)

    def check_securitygroup_ec2_rfc1918(self, sg_item):
        """
        alert if EC2 SG contains RFC1918 CIDRS
        Deprecated as EC2 Classic is gone.
        """
        tag = "Non-VPC Security Group contains private RFC-1918 CIDR"
        severity = 5

        if sg_item.config.get("vpc_id", None):
            return

        multiplier = _check_empty_security_group(sg_item)

        for rule in sg_item.config.get("rules", []):
            cidr = rule.get("cidr_ip", None)
            if cidr and check_rfc_1918(cidr):
                self.add_issue(severity * multiplier, tag, sg_item, notes=cidr)

    def _check_cross_account(self, item, key, recorder, direction='ingress', severity=10):
        """
        Inspects each rule to look for cross account access.

        Called by:
            - check_friendly_cross_account_*
            - check_thirdparty_cross_account_*
            - check_unknown_cross_account_*

        Looks at both CIDR rules and rules referencing other security groups.

        Args:
            item: ChangeItem containing a config member with rules to review.
            key: One of ['FRIENDLY', 'THIRDPARTY', 'UNKNOWN'].  When Auditor::inspect_entity()
                returns a set containing the provided key, the recorder method will be invoked.
            recorder: method to invoke to record an issue.  Should be one of:
                Auditor::record_friendly_access()
                Auditor::record_thirdparty_access()
                Auditor::record_unknown_access()
            direction: Either `ingress` or `egress` matching the rule type to inspect.
            severity: Maximum score to record issue as.  If the SG is not attached
                to any instances, the final final score may be reduced.

        Returns:
            `none`
        """
        multiplier = _check_empty_security_group(item)
        score = severity * multiplier

        for rule in item.config.get("rules", []):
            if rule.get("rule_type") != direction:
                continue

            ports = self._port_for_rule(rule)
            if rule.get('owner_id'):
                entity_value = '{account}/{sg}'.format(account=rule.get('owner_id'), sg=rule.get('group_id'))
                entity = Entity(category='security_group', value=entity_value)
                if key in self.inspect_entity(entity, item):
                    recorder(item, entity, ports, score=score, source='security_group')

            if rule.get('cidr_ip'):
                if '/0' in rule.get('cidr_ip'):
                    continue

                entity = Entity(category='cidr', value=rule.get('cidr_ip'))
                if key in self.inspect_entity(entity, item):
                    recorder(item, entity, ports, score=score, source='security_group')

    def check_friendly_cross_account_ingress(self, item):
        self._check_cross_account(item, 'FRIENDLY', self.record_friendly_access, severity=0)

    def check_friendly_cross_account_egress(self, item):
        self._check_cross_account(item, 'FRIENDLY', self.record_friendly_access, direction='egress', severity=0)

    def check_thirdparty_cross_account_ingress(self, item):
        self._check_cross_account(item, 'THIRDPARTY', self.record_thirdparty_access, severity=0)

    def check_thirdparty_cross_account_egress(self, item):
        self._check_cross_account(item, 'THIRDPARTY', self.record_thirdparty_access, direction='egress', severity=0)

    def check_unknown_cross_account_ingress(self, item):
        self._check_cross_account(item, 'UNKNOWN', self.record_unknown_access, severity=10)

    def check_unknown_cross_account_egress(self, item):
        self._check_cross_account(item, 'UNKNOWN', self.record_unknown_access, direction='egress', severity=10)

    def _check_internet_cidr(self, cidr):
        return str(cidr).endswith('/0')

    def _check_internet_accessible(self, item, direction='ingress', severity=10):
        """
        Make sure the SG does not contain any 0.0.0.0/0 or ::/0 rules.

        Called by:
            check_internet_accessible_ingress()
            check_internet_accessible_egress()

        Returns:
            `none`
        """
        multiplier = _check_empty_security_group(item)
        score = severity * multiplier

        for rule in item.config.get("rules", []):
            if not rule.get("rule_type") == direction:
                continue

            cidr = rule.get("cidr_ip")
            if not self._check_internet_cidr(cidr):
                continue

            actions = self._port_for_rule(rule)
            entity = Entity(category='cidr', value=cidr)
            self.record_internet_access(item, entity, actions, score=score, source='security_group')

    def check_internet_accessible_ingress(self, item):
        self._check_internet_accessible(item, direction='ingress')

    def check_internet_accessible_egress(self, item):
        self._check_internet_accessible(item, direction='egress')
