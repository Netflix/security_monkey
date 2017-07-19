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
.. module: security_monkey.auditors.elbv2
    :platform: Unix

.. version:: $$VERSION$$
.. moduleauthor::  Patrick Kelley <pkelley@netflix.com> @monkeysecurity

"""
from security_monkey.watchers.elbv2 import ELBv2
from security_monkey.auditor import Auditor
from security_monkey.watchers.security_group import SecurityGroup
from security_monkey.common.utils import check_rfc_1918
from security_monkey.datastore import NetworkWhitelistEntry

import ipaddr


class ELBv2Auditor(Auditor):
    index = ELBv2.index
    i_am_singular = ELBv2.i_am_singular
    i_am_plural = ELBv2.i_am_plural
    network_whitelist = []
    support_watcher_indexes = [SecurityGroup.index]

    def __init__(self, accounts=None, debug=False):
        super(ELBv2Auditor, self).__init__(accounts=accounts, debug=debug)

    def prep_for_audit(self):
        self.network_whitelist = NetworkWhitelistEntry.query.all()

    def _check_inclusion_in_network_whitelist(self, cidr):
        for entry in self.network_whitelist:
            if ipaddr.IPNetwork(cidr) in ipaddr.IPNetwork(str(entry.cidr)):
                return True
        return False
    
    def check_internet_facing(self, alb):
        scheme = alb.config.get('Scheme')
        if scheme == 'internet-facing':
            # Grab each attached security group and determine if they contain
            # a public IP
            security_groups = alb.config.get('SecurityGroups', [])
            sg_items = self.get_watcher_support_items(SecurityGroup.index, alb.account)
            for sgid in security_groups:
                for sg in sg_items:
                    if sg.config.get('id') == sgid:
                        sg_cidrs = set()
                        internet_accessible_cidrs = set()
                        for rule in sg.config.get('rules', []):
                            cidr = rule.get('cidr_ip', '')

                            if rule.get('rule_type', None) == 'ingress' and cidr:
                                if cidr.endswith('/0'):
                                    internet_accessible_cidrs.add(cidr)
                                elif not check_rfc_1918(cidr) and not self._check_inclusion_in_network_whitelist(cidr):
                                    sg_cidrs.add(cidr)

                        if sg_cidrs:
                            notes = 'SG [{sgname}] via [{cidr}]'.format(
                                sgname=sg.name,
                                cidr=', '.join(sg_cidrs))
                            self.add_issue(1, 'ALB accessible from non-private CIDR.', alb, notes=notes)

                        if internet_accessible_cidrs:
                            notes = 'SG [{sgname}] via [{cidr}]'.format(
                                sgname=sg.name,
                                cidr=', '.join(internet_accessible_cidrs))
                            self.add_issue(1, 'ALB is Internet accessible.', alb, notes=notes)

                        break

    def check_logging(self, alb):
        attributes = alb.config.get('Attributes', [])
        for attribute in attributes:
            if attribute.get('Key') == 'access_logs.s3.enabled':
                if attribute['Value'] == 'false':
                    self.add_issue(1, 'ALB is not configured for logging.', alb)
                return

    def check_deletion_protection(self, alb):
        attributes = alb.config.get('Attributes', [])
        for attribute in attributes:
            if attribute.get('Key') == 'deletion_protection.enabled':
                if attribute['Value'] == 'false':
                    self.add_issue(1, 'ALB is not configured for deletion protection.', alb)
                return

    def check_ssl_policy(self, alb):
        """
        ALB SSL Policies are much simpler than ELB (classic) policies.
        - Custom policies are not allowed.
        - Try to use ELBSecurityPolicy-2016-08
        - Alert on unknown policy or if using ELBSecurityPolicy-TLS-1-0-2015-04
        - The ELBSecurityPolicy-2016-08 and ELBSecurityPolicy-2015-05 security policies for Application Load Balancers are identical.

        http://docs.aws.amazon.com/elasticloadbalancing/latest/application/create-https-listener.html#describe-ssl-policies
        """
        supported_ssl_policies = set([
            'ELBSecurityPolicy-2016-08',
            'ELBSecurityPolicy-TLS-1-2-2017-01',
            'ELBSecurityPolicy-TLS-1-1-2017-01',
            'ELBSecurityPolicy-2015-05',
            'ELBSecurityPolicy-TLS-1-0-2015-04'])

        for listener in alb.config.get('Listeners', []):
            port = listener.get('Port')
            ssl_policy = listener.get('SslPolicy')
            if not ssl_policy:
                continue

            if ssl_policy == 'ELBSecurityPolicy-TLS-1-0-2015-04':
                notes = 'Policy {0} on port {1}'.format(ssl_policy, port)
                self.add_issue(5,
                    'ELBSecurityPolicy-TLS-1-0-2015-04 contains a weaker cipher (DES-CBC3-SHA) '
                    'for backwards compatibility with Windows XP systems. Vulnerable to SWEET32 CVE-2016-2183.',
                    alb, notes=notes)

            if ssl_policy not in supported_ssl_policies:
                self.add_issue(10, 'Unknown reference policy.', alb, notes=ssl_policy)