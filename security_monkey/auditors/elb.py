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
.. module: security_monkey.auditors.elb
    :platform: Unix

.. version:: $$VERSION$$
.. moduleauthor::  Patrick Kelley <pkelley@netflix.com> @monkeysecurity

"""
from security_monkey.watchers.elb import ELB
from security_monkey.auditor import Auditor, Categories
from security_monkey.common.utils import check_rfc_1918
from security_monkey.datastore import NetworkWhitelistEntry
from security_monkey.datastore import Item
from security_monkey.watchers.security_group import SecurityGroup
from collections import defaultdict

import json
import re

# From https://docs.aws.amazon.com/ElasticLoadBalancing/latest/DeveloperGuide/elb-security-policy-table.html
DEPRECATED_CIPHERS = [
    'RC2-CBC-MD5',
    'PSK-AES256-CBC-SHA',
    'PSK-3DES-EDE-CBC-SHA',
    'KRB5-DES-CBC3-SHA',
    'KRB5-DES-CBC3-MD5',
    'PSK-AES128-CBC-SHA',
    'PSK-RC4-SHA',
    'KRB5-RC4-SHA',
    'KRB5-RC4-MD5',
    'KRB5-DES-CBC-SHA',
    'KRB5-DES-CBC-MD5'
]

# EXP- ciphers are export-grade and vulnerable to the FREAK attack: CVE-2015-0204
#  http://aws.amazon.com/security/security-bulletins/ssl-issue--freak-attack-/
EXPORT_CIPHERS = [
    'EXP-EDH-RSA-DES-CBC-SHA',
    'EXP-EDH-DSS-DES-CBC-SHA',
    'EXP-ADH-DES-CBC-SHA',
    'EXP-DES-CBC-SHA',
    'EXP-RC2-CBC-MD5',
    'EXP-KRB5-RC2-CBC-SHA',
    'EXP-KRB5-DES-CBC-SHA',
    'EXP-KRB5-RC2-CBC-MD5',
    'EXP-KRB5-DES-CBC-MD5',
    'EXP-ADH-RC4-MD5',
    'EXP-RC4-MD5',
    'EXP-KRB5-RC4-SHA',
    'EXP-KRB5-RC4-MD5'
]

# These are ciphers that are not enabled in ELBSecurityPolicy-2014-10
NOTRECOMMENDED_CIPHERS = [
    'CAMELLIA128-SHA',
    'EDH-RSA-DES-CBC3-SHA',
    'ECDHE-ECDSA-RC4-SHA',
    'DHE-DSS-AES256-GCM-SHA384',
    'DHE-RSA-AES256-GCM-SHA384',
    'DHE-RSA-AES256-SHA256',
    'DHE-DSS-AES256-SHA256',
    'DHE-RSA-AES256-SHA',
    'DHE-DSS-AES256-SHA',
    'DHE-RSA-CAMELLIA256-SHA',
    'DHE-DSS-CAMELLIA256-SHA',
    'CAMELLIA256-SHA',
    'EDH-DSS-DES-CBC3-SHA',
    'DHE-DSS-AES128-GCM-SHA256',
    'DHE-RSA-AES128-GCM-SHA256',
    'DHE-RSA-AES128-SHA256',
    'DHE-DSS-AES128-SHA256',
    'DHE-RSA-CAMELLIA128-SHA',
    'DHE-DSS-CAMELLIA128-SHA',
    'ADH-AES128-GCM-SHA256',
    'ADH-AES128-SHA',
    'ADH-AES128-SHA256',
    'ADH-AES256-GCM-SHA384',
    'ADH-AES256-SHA',
    'ADH-AES256-SHA256',
    'ADH-CAMELLIA128-SHA',
    'ADH-CAMELLIA256-SHA',
    'ADH-DES-CBC3-SHA',
    'ADH-DES-CBC-SHA',
    'ADH-RC4-MD5',
    'ADH-SEED-SHA',
    'DES-CBC-SHA',
    'DHE-DSS-SEED-SHA',
    'DHE-RSA-SEED-SHA',
    'EDH-DSS-DES-CBC-SHA',
    'EDH-RSA-DES-CBC-SHA',
    'IDEA-CBC-SHA',
    'RC4-MD5',
    'SEED-SHA',
    'DES-CBC3-MD5',
    'DES-CBC-MD5',

    # These two are in ELBSecurityPolicy-2014-10, but they contain RC4.
    # They were removed in ELBSecurityPolicy-2015-02.
    # Flag any custom listener policies using these ciphers.
    # https://forums.aws.amazon.com/ann.jspa?annID=2877
    'RC4-SHA',
    'ECDHE-RSA-RC4-SHA',

    # Removed in ELBSecurityPolicy-2015-05 likely to mitigate logjam CVE-2015-400
    # https://forums.aws.amazon.com/ann.jspa?annID=3061
    'DHE-DSS-AES128-SHA',

    # Removed in 2014-01, Reintroduced in 2015-03, Removed again in 2016-08
    # SWEET32 CVE-2016-2183
    # https://forums.aws.amazon.com/ann.jspa?annID=3996
    'DES-CBC3-SHA'
]


class ELBAuditor(Auditor):
    index = ELB.index
    i_am_singular = ELB.i_am_singular
    i_am_plural = ELB.i_am_plural
    # support_watcher_indexes = [SecurityGroup.index]
    support_auditor_indexes = [SecurityGroup.index]

    def __init__(self, accounts=None, debug=False):
        super(ELBAuditor, self).__init__(accounts=accounts, debug=debug)

    def _get_listener_ports_and_protocols(self, item):
        """
        "ListenerDescriptions": [
            {
              "LoadBalancerPort": 80,
              "Protocol": "HTTP",
            },
            {
              "Protocol": "HTTPS",
              "LoadBalancerPort": 443,
            }
        """
        protocol_and_ports = defaultdict(set)
        for listener in item.config.get('ListenerDescriptions', []):
            protocol = listener.get('Protocol')
            if not protocol:
                continue
            if protocol == '-1':
                protocol = 'ALL_PROTOCOLS'
            elif 'HTTP' in protocol:
                protocol = 'TCP'
            protocol_and_ports[protocol].add(listener.get('LoadBalancerPort'))
        return protocol_and_ports

    def check_internet_scheme(self, elb_item):
        """
        alert when an ELB has an "internet-facing" scheme
        and a security group containing ingress issues on a listener port.
        -   Friendly Cross Account
        -   Thirdparty Cross Account
        -   Unknown Access
        -   Internet Accessible
        """
        scheme = elb_item.config.get('Scheme', None)
        vpc = elb_item.config.get('VPCId', None)
        if scheme and scheme == "internet-facing" and not vpc:
            self.add_issue(1, Categories.INTERNET_ACCESSIBLE, elb_item, notes='EC2 Classic ELB has internet-facing scheme.')
        elif scheme and scheme == "internet-facing" and vpc:
            security_group_ids = set(elb_item.config.get('SecurityGroups', []))
            sg_auditor_items = self.get_auditor_support_items(SecurityGroup.index, elb_item.account)
            security_auditor_groups = [sg for sg in sg_auditor_items if sg.config.get('id') in security_group_ids]

            for sg in security_auditor_groups:
                for issue in sg.db_item.issues:
                    if self._issue_matches_listeners(elb_item, issue):
                        self.link_to_support_item_issues(elb_item, sg.db_item,
                            sub_issue_message=issue.issue, score=issue.score)

    def check_listener_reference_policy(self, elb_item):
        """
        alert when an SSL listener is not using the latest reference policy.
        """
        policy_port_map = defaultdict(list)
        for listener in elb_item.config.get('ListenerDescriptions', []):
            if len(listener.get('PolicyNames', [])) > 0:
                for name in listener.get('PolicyNames', []):
                    policy_port_map[name].append(listener['LoadBalancerPort'])

        policies = elb_item.config.get('PolicyDescriptions', {})
        for policy_name, policy in list(policies.items()):
            policy_type = policy.get("type", None)
            if policy_type and policy_type == "SSLNegotiationPolicyType":
                reference_policy = policy.get('reference_security_policy', None)
                self._process_reference_policy(reference_policy, policy_name, json.dumps(policy_port_map[policy_name]), elb_item)
                if not reference_policy:
                    self._process_custom_listener_policy(policy_name, policy, json.dumps(policy_port_map[policy_name]), elb_item)

    def check_logging(self, elb_item):
        """
        Alert when elb logging is not enabled
        """
        logging = elb_item.config.get('Attributes', {}).get('AccessLog', {})
        if not logging:
            self.add_issue(1, Categories.RECOMMENDATION, elb_item, notes='Enable access logs')
            return

        if not logging.get('Enabled'):
            self.add_issue(1, Categories.RECOMMENDATION, elb_item, notes='Enable access logs')
            return

    def _process_reference_policy(self, reference_policy, policy_name, ports, elb_item):
        if reference_policy is None:
            notes = Categories.INSECURE_TLS_NOTES.format(
                policy=policy_name, port=ports,
                reason="Custom listener policies discouraged")
            self.add_issue(8, Categories.INSECURE_TLS, elb_item, notes=notes)
            return

        if reference_policy == 'ELBSecurityPolicy-2011-08':
            notes = Categories.INSECURE_TLS_NOTES.format(
                policy=reference_policy, port=ports,
                reason="Vulnerable and deprecated")
            self.add_issue(10, Categories.INSECURE_TLS, elb_item, notes=notes)

            notes = Categories.INSECURE_TLS_NOTES.format(
                policy=reference_policy, port=ports,
                reason="Vulnerable to poodlebleed")
            self.add_issue(10, Categories.INSECURE_TLS, elb_item, notes=notes)

            notes = Categories.INSECURE_TLS_NOTES.format(
                policy=reference_policy, port=ports,
                reason="Lacks server order cipher preference")
            self.add_issue(10, Categories.INSECURE_TLS, elb_item, notes=notes)

            notes = Categories.INSECURE_TLS_NOTES.format(
                policy=reference_policy, port=ports,
                reason="Contains RC4 ciphers (RC4-SHA)")
            self.add_issue(10, Categories.INSECURE_TLS, elb_item, notes=notes)

            notes = Categories.INSECURE_TLS_NOTES_2.format(
                policy=reference_policy, port=ports,
                reason='Weak cipher (DES-CBC3-SHA) for Windows XP support',
                cve='SWEET32 CVE-2016-2183')
            self.add_issue(5, Categories.INSECURE_TLS, elb_item, notes=notes)

            return

        if reference_policy == 'ELBSecurityPolicy-2014-01':
            # Massively different cipher suite than 2011-08
            # Introduces Server Order Preference
            notes = Categories.INSECURE_TLS_NOTES.format(
                policy=reference_policy, port=ports,
                reason="Vulnerable to poodlebleed")
            self.add_issue(10, Categories.INSECURE_TLS, elb_item, notes=notes)

            notes = Categories.INSECURE_TLS_NOTES_2.format(
                policy=reference_policy, port=ports,
                reason="Uses diffie-hellman (DHE-DSS-AES1280SHA)",
                cve='LOGJAM CVE-2015-4000')
            self.add_issue(5, Categories.INSECURE_TLS, elb_item, notes=notes)
            
            notes = Categories.INSECURE_TLS_NOTES.format(
                policy=reference_policy, port=ports,
                reason="Contains RC4 ciphers (ECDHE-RSA-RC4-SHA and RC4-SHA)")
            self.add_issue(10, Categories.INSECURE_TLS, elb_item, notes=notes)
            return

        if reference_policy == 'ELBSecurityPolicy-2014-10':
            # Dropped SSLv3 to stop Poodlebleed CVE-2014-3566
            # https://aws.amazon.com/security/security-bulletins/CVE-2014-3566-advisory/
            notes = Categories.INSECURE_TLS_NOTES.format(
                policy=reference_policy, port=ports,
                reason="Contains RC4 ciphers (ECDHE-RSA-RC4-SHA and RC4-SHA)")
            self.add_issue(10, Categories.INSECURE_TLS, elb_item, notes=notes)

            notes = Categories.INSECURE_TLS_NOTES_2.format(
                policy=reference_policy, port=ports,
                reason="Uses diffie-hellman (DHE-DSS-AES1280SHA)",
                cve='LOGJAM CVE-2015-4000')
            self.add_issue(5, Categories.INSECURE_TLS, elb_item, notes=notes)

            return

        if reference_policy == 'ELBSecurityPolicy-2015-02':
            # Yay! Dropped RC4, but broke Windows XP.
            # https://forums.aws.amazon.com/ann.jspa?annID=2877
            self.add_issue(0, Categories.INFORMATIONAL, elb_item, 
                notes="ELBSecurityPolicy-2015-02 is not Windows XP compatible")

            notes = Categories.INSECURE_TLS_NOTES.format(
                policy=reference_policy, port=ports,
                reason="Uses diffie-hellman (DHE-DSS-AES1280SHA)",
                cve='LOGJAM CVE-2015-4000')
            self.add_issue(5, Categories.INSECURE_TLS, elb_item, notes=notes)
            return

        if reference_policy == 'ELBSecurityPolicy-2015-03':
            # Re-introduced DES-CBC3-SHA so Windows XP would work again.
            notes = Categories.INSECURE_TLS_NOTES_2.format(
                policy=reference_policy, port=ports,
                reason='Weak cipher (DES-CBC3-SHA) for Windows XP support',
                cve='SWEET32 CVE-2016-2183')
            self.add_issue(5, Categories.INSECURE_TLS, elb_item, notes=notes)
            
            notes = Categories.INSECURE_TLS_NOTES_2.format(
                policy=reference_policy, port=ports,
                reason="Uses diffie-hellman (DHE-DSS-AES1280SHA)",
                cve='LOGJAM CVE-2015-4000')
            self.add_issue(5, Categories.INSECURE_TLS, elb_item, notes=notes)
            return

        if reference_policy == 'ELBSecurityPolicy-2015-05':
            # Yay! - Removes diffie-hellman (DHE-DSS-AES128-SHA), likely to mitigate logjam CVE-2015-400
            # https://forums.aws.amazon.com/ann.jspa?annID=3061
            notes = Categories.INSECURE_TLS_NOTES_2.format(
                policy=reference_policy, port=ports,
                reason='Weak cipher (DES-CBC3-SHA) for Windows XP support',
                cve='SWEET32 CVE-2016-2183')
            self.add_issue(5, Categories.INSECURE_TLS, elb_item, notes=notes)
            return

        if reference_policy == 'ELBSecurityPolicy-2016-08':
            # Yay! - Removes DES-CBC3-SHA in response to SWEET32 CVE-2016-2183
            # https://forums.aws.amazon.com/ann.jspa?annID=3996
            return

        if reference_policy == 'ELBSecurityPolicy-TLS-1-1-2017-01' or reference_policy == 'ELBSecurityPolicy-TLS-1-2-2017-01':
            # Transitional policies for early TLS deprecation
            # https://forums.aws.amazon.com/ann.jspa?annID=4475
            return

        notes = Categories.INSECURE_TLS_NOTES.format(policy=reference_policy, port=ports, reason='Unknown reference policy')
        self.add_issue(10, Categories.INSECURE_TLS, elb_item, notes=notes)

    def _process_custom_listener_policy(self, policy_name, policy, ports, elb_item):
        """
        Alerts on:
            sslv2
            sslv3
            missing server order preference
            deprecated ciphers
        """
        if policy.get('protocols', {}).get('sslv2', None):
            notes = Categories.INSECURE_TLS_NOTES.format(
                policy=policy_name, port=ports,
                reason='SSLv2 is enabled')
            self.add_issue(10, Categories.INSECURE_TLS, elb_item, notes=notes)

        if policy.get('protocols', {}).get('sslv3', None):
            notes = Categories.INSECURE_TLS_NOTES.format(
                policy=policy_name, port=ports,
                reason='SSLv3 is enabled')
            self.add_issue(10, Categories.INSECURE_TLS, elb_item, notes=notes)

        server_defined_cipher_order = policy.get('server_defined_cipher_order', None)
        if server_defined_cipher_order is False:
            notes = Categories.INSECURE_TLS_NOTES.format(
                policy=policy_name, port=ports,
                reason="Server defined cipher order is disabled")
            self.add_issue(10, Categories.INSECURE_TLS, elb_item, notes=notes)

        for cipher in policy['supported_ciphers']:
            if cipher in EXPORT_CIPHERS:
                # CVE-2015-0204
                # https://aws.amazon.com/security/security-bulletins/ssl-issue--freak-attack-/
                notes = Categories.INSECURE_TLS_NOTES_2.format(
                    policy=policy_name, port=ports,
                    reason='Export grade cipher ({cipher})'.format(cipher=cipher),
                    cve="FREAK CVE-2015-0204")
                self.add_issue(10, Categories.INSECURE_TLS, elb_item, notes=notes)

            if cipher in DEPRECATED_CIPHERS:
                notes = Categories.INSECURE_TLS_NOTES.format(
                    policy=policy_name, port=ports,
                    reason='Deprecated cipher ({cipher})'.format(cipher=cipher))
                self.add_issue(10, Categories.INSECURE_TLS, elb_item, notes=notes)

            if cipher in NOTRECOMMENDED_CIPHERS:
                notes = Categories.INSECURE_TLS_NOTES.format(
                    policy=policy_name, port=ports,
                    reason='Cipher not recommended ({cipher})'.format(cipher=cipher))
                self.add_issue(10, Categories.INSECURE_TLS, elb_item, notes=notes)
