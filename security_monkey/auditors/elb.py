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
from security_monkey.auditor import Auditor
from security_monkey.common.utils import check_rfc_1918
from security_monkey.datastore import NetworkWhitelistEntry
from security_monkey.datastore import Item
from security_monkey.watchers.security_group import SecurityGroup
from collections import defaultdict

import ipaddr
import json

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
    network_whitelist = []
    support_watcher_indexes = [SecurityGroup.index]

    def __init__(self, accounts=None, debug=False):
        super(ELBAuditor, self).__init__(accounts=accounts, debug=debug)

    def prep_for_audit(self):
        self.network_whitelist = NetworkWhitelistEntry.query.all()

    def _check_inclusion_in_network_whitelist(self, cidr):
        for entry in self.network_whitelist:
            if ipaddr.IPNetwork(cidr) in ipaddr.IPNetwork(str(entry.cidr)):
                return True
        return False

    def check_internet_scheme(self, elb_item):
        """
        alert when an ELB has an "internet-facing" scheme.
        """
        scheme = elb_item.config.get('Scheme', None)
        vpc = elb_item.config.get('VPCId', None)
        if scheme and scheme == u"internet-facing" and not vpc:
            self.add_issue(1, 'ELB is Internet accessible.', elb_item)
        elif scheme and scheme == u"internet-facing" and vpc:
            # Grab each attached security group and determine if they contain
            # a public IP
            security_groups = elb_item.config.get('SecurityGroups', [])
            sg_items = self.get_watcher_support_items(SecurityGroup.index, elb_item.account)
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
                            self.add_issue(1, 'VPC ELB accessible from non-private CIDR.', elb_item, notes=notes)

                        if internet_accessible_cidrs:
                            notes = 'SG [{sgname}] via [{cidr}]'.format(
                                sgname=sg.name,
                                cidr=', '.join(internet_accessible_cidrs))
                            self.add_issue(1, 'VPC ELB is Internet accessible.', elb_item, notes=notes)

                        break

    def check_listener_reference_policy(self, elb_item):
        """
        alert when an SSL listener is not using the latest reference policy.
        """
        policy_port_map = defaultdict(list)
        if elb_item.config.get('ListenerDescriptions'):
            for listener in elb_item.config.get('ListenerDescriptions'):
                if len(listener.get('PolicyNames', [])) > 0:
                    for name in listener.get('PolicyNames', []):
                        policy_port_map[name].append(listener['LoadBalancerPort'])

        policies = elb_item.config.get('PolicyDescriptions')
        for policy_name, policy in policies.items():
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
            self.add_issue(1, 'ELB is not configured for logging.', elb_item)
            return

        if not logging.get('Enabled'):
            self.add_issue(1, 'ELB is not configured for logging.', elb_item)
            return

    def _process_reference_policy(self, reference_policy, policy_name, port, elb_item):
        notes = "Policy {0} on port {1}".format(policy_name, port)
        if reference_policy is None:
            self.add_issue(8, "Custom listener policies are discouraged.", elb_item, notes=notes)
            return

        if reference_policy == 'ELBSecurityPolicy-2011-08':
            self.add_issue(10, "ELBSecurityPolicy-2011-08 is vulnerable and deprecated", elb_item, notes=notes)
            self.add_issue(10, "ELBSecurityPolicy-2011-08 is vulnerable to poodlebleed", elb_item, notes=notes)
            self.add_issue(10, "ELBSecurityPolicy-2011-08 lacks server order cipher preference.", elb_item, notes=notes)
            self.add_issue(10, "ELBSecurityPolicy-2011-08 contains RC4 ciphers "
                           "(RC4-SHA) that have been removed in newer policies.", elb_item, notes=notes)
            self.add_issue(5, "ELBSecurityPolicy-2011-08 contains a weaker cipher (DES-CBC3-SHA) "
                           "for backwards compatibility with Windows XP systems. Vulnerable to SWEET32 CVE-2016-2183.", elb_item, notes=notes)
            return

        if reference_policy == 'ELBSecurityPolicy-2014-01':
            # Massively different cipher suite than 2011-08
            # Introduces Server Order Preference
            self.add_issue(10, "ELBSecurityPolicy-2014-01 is vulnerable to poodlebleed", elb_item, notes=notes)
            self.add_issue(5, "ELBSecurityPolicy-2014-01 uses diffie-hellman (DHE-DSS-AES1280SHA). "
                           "Vulnerable to LOGJAM CVE-2015-4000.", elb_item, notes=notes)
            self.add_issue(10, "ELBSecurityPolicy-2014-01 contains RC4 ciphers "
                           "(ECDHE-RSA-RC4-SHA and RC4-SHA) that have been removed in newer policies.", elb_item, notes=notes)
            return

        if reference_policy == 'ELBSecurityPolicy-2014-10':
            # Dropped SSLv3 to stop Poodlebleed CVE-2014-3566
            # https://aws.amazon.com/security/security-bulletins/CVE-2014-3566-advisory/
            self.add_issue(10, "ELBSecurityPolicy-2014-10 contains RC4 ciphers "
                           "(ECDHE-RSA-RC4-SHA and RC4-SHA) that have been removed in newer policies.", elb_item, notes=notes)
            self.add_issue(5, "ELBSecurityPolicy-2014-10 uses diffie-hellman (DHE-DSS-AES1280SHA). "
                           "Vulnerable to LOGJAM CVE-2015-4000.", elb_item, notes=notes)
            return

        if reference_policy == 'ELBSecurityPolicy-2015-02':
            # Yay! Dropped RC4, but broke Windows XP.
            # https://forums.aws.amazon.com/ann.jspa?annID=2877
            self.add_issue(0, "ELBSecurityPolicy-2015-02 is not compatible with Windows XP systems.", elb_item, notes=notes)
            self.add_issue(5, "ELBSecurityPolicy-2015-02 uses diffie-hellman (DHE-DSS-AES1280SHA). "
                           "Vulnerable to LOGJAM CVE-2015-4000.", elb_item, notes=notes)
            return

        if reference_policy == 'ELBSecurityPolicy-2015-03':
            # Re-introduced DES-CBC3-SHA so Windows XP would work again.
            self.add_issue(0, "ELBSecurityPolicy-2015-03 contains a weaker cipher (DES-CBC3-SHA) "
                           "for backwards compatibility with Windows XP systems. Vulnerable to SWEET32 CVE-2016-2183.", elb_item, notes=notes)
            self.add_issue(5, "ELBSecurityPolicy-2015-03 uses diffie-hellman (DHE-DSS-AES1280SHA). "
                           "Vulnerable to LOGJAM CVE-2015-4000.", elb_item, notes=notes)
            return

        if reference_policy == 'ELBSecurityPolicy-2015-05':
            # Yay! - Removes diffie-hellman (DHE-DSS-AES128-SHA), likely to mitigate logjam CVE-2015-400
            # https://forums.aws.amazon.com/ann.jspa?annID=3061
            self.add_issue(0, "ELBSecurityPolicy-2015-03 contains a weaker cipher (DES-CBC3-SHA) "
                           "for backwards compatibility with Windows XP systems. Vulnerable to SWEET32 CVE-2016-2183", elb_item, notes=notes)
            return

        if reference_policy == 'ELBSecurityPolicy-2016-08':
            # Yay! - Removes DES-CBC3-SHA in response to SWEET32 CVE-2016-2183
            # https://forums.aws.amazon.com/ann.jspa?annID=3996
            return

        if reference_policy == 'ELBSecurityPolicy-TLS-1-1-2017-01' or reference_policy == 'ELBSecurityPolicy-TLS-1-2-2017-01':
            # Transitional policies for early TLS deprecation
            # https://forums.aws.amazon.com/ann.jspa?annID=4475
            return

        notes = reference_policy
        self.add_issue(10, "Unknown reference policy.", elb_item, notes=notes)

    def _process_custom_listener_policy(self, policy_name, policy, port, elb_item):
        """
        Alerts on:
            sslv2
            sslv3
            missing server order preference
            deprecated ciphers
        """
        notes = "Policy {0} on port {1}".format(policy_name, port)

        if policy.get('protocols', {}).get('sslv2', None):
            self.add_issue(10, "SSLv2 is enabled", elb_item, notes=notes)

        if policy.get('protocols', {}).get('sslv3', None):
            self.add_issue(10, "SSLv3 is enabled", elb_item, notes=notes)

        server_defined_cipher_order = policy.get('server_defined_cipher_order', None)
        if server_defined_cipher_order is False:
            self.add_issue(10, "Server Defined Cipher Order is Disabled.", elb_item, notes=notes)

        for cipher in policy['supported_ciphers']:
            if cipher in EXPORT_CIPHERS:
                c_notes = "{0} - {1}".format(notes, cipher)
                # CVE-2015-0204
                # https://aws.amazon.com/security/security-bulletins/ssl-issue--freak-attack-/
                self.add_issue(10, "Export Grade Cipher Used. Vuln to FREAK attack.", elb_item, notes=c_notes)

            if cipher in DEPRECATED_CIPHERS:
                c_notes = "{0} - {1}".format(notes, cipher)
                self.add_issue(10, "Deprecated Cipher Used.", elb_item, notes=c_notes)

            if cipher in NOTRECOMMENDED_CIPHERS:
                c_notes = "{0} - {1}".format(notes, cipher)
                self.add_issue(10, "Cipher Not Recommended.", elb_item, notes=c_notes)
