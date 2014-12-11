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
    'KRB5-DES-CBC-MD5',
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
    'DES-CBC3-SHA',
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
    'DES-CBC-MD5'
]

class ELBAuditor(Auditor):
    index = ELB.index
    i_am_singular = ELB.i_am_singular
    i_am_plural = ELB.i_am_plural

    def __init__(self, accounts=None, debug=False):
        super(ELBAuditor, self).__init__(accounts=accounts, debug=debug)

    def check_internet_scheme(self, elb_item):
        """
        alert when an ELB has an "internet-facing" scheme.
        """
        scheme = elb_item.config.get('scheme', None)
        if scheme and scheme == u"internet-facing":
            self.add_issue(1, 'ELB is Internet accessible.', elb_item)

    def check_listener_reference_policy(self, elb_item):
        """
        alert when an SSL listener is not using the ELBSecurity Policy-2014-10 policy.
        """
        listeners = elb_item.config.get('listeners')
        for listener in listeners:
            for policy in listener['policies']:
                policy_type = policy.get("type", None)
                if policy_type and policy_type == "SSLNegotiationPolicyType":
                    reference_policy = policy.get('reference_security_policy', None)
                    self._process_reference_policy(reference_policy, policy['name'], listener['load_balancer_port'], elb_item)
                    if not reference_policy:
                        self._process_custom_listener_policy(policy, listener['load_balancer_port'], elb_item)

    def _process_reference_policy(self, reference_policy, policy_name, port, elb_item):
        notes = "Policy {0} on port {1}".format(policy_name, port)
        if reference_policy is None:
            self.add_issue(8, "Custom listener policies are discouraged.", elb_item, notes=notes)
            return

        if reference_policy == 'ELBSecurityPolicy-2011-08':
            self.add_issue(10, "ELBSecurityPolicy-2011-08 is vulnerable and deprecated", elb_item, notes=notes)
            return

        if reference_policy == 'ELBSecurityPolicy-2014-01':
            self.add_issue(10, "ELBSecurityPolicy-2014-01 is vulnerable to poodlebleed", elb_item, notes=notes)
            return

        if reference_policy == 'ELBSecurityPolicy-2014-10':
            # Yay!
            return

        notes=reference_policy
        self.add_issue(10, "Unknown reference policy.", elb_item, notes=notes)

    def _process_custom_listener_policy(self, policy, port, elb_item):
        """
        Alerts on:
            sslv2
            sslv3
            missing server order preference
            deprecated ciphers
        """
        notes = "Policy {0} on port {1}".format(policy['name'], port)

        if policy.get('sslv2', None):
            self.add_issue(10, "SSLv2 is enabled", elb_item, notes=notes)

        if policy.get('sslv3', None):
            self.add_issue(10, "SSLv3 is enabled", elb_item, notes=notes)

        server_defined_cipher_order = policy.get('server_defined_cipher_order', None)
        if server_defined_cipher_order is False:
            self.add_issue(10, "Server Defined Cipher Order is Disabled.", elb_item, notes=notes)

        for cipher in policy['supported_ciphers']:
            if cipher in DEPRECATED_CIPHERS:
                c_notes = "{0} - {1}".format(notes, cipher)
                self.add_issue(10, "Deprecated Cipher Used.", elb_item, notes=c_notes)

            if cipher in NOTRECOMMENDED_CIPHERS:
                c_notes = "{0} - {1}".format(notes, cipher)
                self.add_issue(10, "Cipher Not Recommended.", elb_item, notes=c_notes)


