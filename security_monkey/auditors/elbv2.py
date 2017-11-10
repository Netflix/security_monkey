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
from security_monkey.auditor import Auditor, Categories
from security_monkey.watchers.security_group import SecurityGroup
from security_monkey.common.utils import check_rfc_1918
from security_monkey.datastore import NetworkWhitelistEntry

from collections import defaultdict
import re


class ELBv2Auditor(Auditor):
    index = ELBv2.index
    i_am_singular = ELBv2.i_am_singular
    i_am_plural = ELBv2.i_am_plural
    # support_watcher_indexes = [SecurityGroup.index]
    support_auditor_indexes = [SecurityGroup.index]

    def __init__(self, accounts=None, debug=False):
        super(ELBv2Auditor, self).__init__(accounts=accounts, debug=debug)

    def _get_listener_ports_and_protocols(self, item):
        """
        "Listeners": [
            {
              "Protocol": "HTTP",
              "Port": 80,
            }
          ],
        """
        protocol_and_ports = defaultdict(set)
        for listener in item.config.get('Listeners', []):
            protocol = listener.get('Protocol')
            if not protocol:
                continue
            if protocol == '-1':
                protocol = 'ALL_PROTOCOLS'
            elif 'HTTP' in protocol:
                protocol = 'TCP'
            protocol_and_ports[protocol].add(listener.get('Port'))
        return protocol_and_ports

    def check_internet_facing(self, alb):
        scheme = alb.config.get('Scheme')
        if scheme == 'internet-facing':
            security_group_ids = set(alb.config.get('SecurityGroups', []))
            sg_auditor_items = self.get_auditor_support_items(SecurityGroup.index, alb.account)
            security_auditor_groups = [sg for sg in sg_auditor_items if sg.config.get('id') in security_group_ids]

            for sg in security_auditor_groups:
                for issue in sg.db_item.issues:
                    if self._issue_matches_listeners(alb, issue):
                        self.link_to_support_item_issues(alb, sg.db_item,
                            sub_issue_message=issue.issue, score=issue.score)

    def check_logging(self, alb):
        attributes = alb.config.get('Attributes', [])
        for attribute in attributes:
            if attribute.get('Key') == 'access_logs.s3.enabled':
                if attribute['Value'] == 'false':
                    self.add_issue(1, Categories.RECOMMENDATION, alb, notes='Enable access logs')
                return

    def check_deletion_protection(self, alb):
        attributes = alb.config.get('Attributes', [])
        for attribute in attributes:
            if attribute.get('Key') == 'deletion_protection.enabled':
                if attribute['Value'] == 'false':
                    self.add_issue(1, Categories.RECOMMENDATION, alb, notes='Enable deletion protection')
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
            port = '['+str(listener.get('Port'))+']'
            ssl_policy = listener.get('SslPolicy')
            if not ssl_policy:
                continue

            if ssl_policy == 'ELBSecurityPolicy-TLS-1-0-2015-04':
                notes = Categories.INSECURE_TLS_NOTES_2.format(
                    policy=ssl_policy, port=port,
                    reason='Weak cipher (DES-CBC3-SHA) for Windows XP support',
                    cve='SWEET32 CVE-2016-2183')
                self.add_issue(5, Categories.INSECURE_TLS, alb, notes=notes)

            if ssl_policy not in supported_ssl_policies:
                notes = Categories.INSECURE_TLS_NOTES.format(policy=ssl_policy, port=port, reason='Unknown reference policy')
                self.add_issue(10, Categories.INSECURE_TLS, alb, notes=notes)
