#     Copyright 2017 Google, Inc.
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
from security_monkey.tests import SecurityMonkeyTestCase

"""
.. module: security_monkey.tests.auditors.gcp.gce.test_firewall
    :platform: Unix

.. version:: $$VERSION$$
.. moduleauthor::  Tom Melendez <supertom@google.com> @supertom
"""

ALLOWED_LIST_WITH_PORTRANGE = [
    {
     "IPProtocol": "tcp",
     "ports": [
      "0-65535"
     ]
    },
    {
     "IPProtocol": "udp",
     "ports": [
      "0-65535"
     ]
    },
    {
     "IPProtocol": "icmp"
    }
   ]

ALLOWED_LIST_NO_PORTRANGE = [
    {
     "IPProtocol": "tcp",
     "ports": [
      "80"
     ]
    },
    {
     "IPProtocol": "icmp"
    }
   ]

SOURCERANGES_PRESENT = [
    '0.0.0.0/0',
    '192.168.1.0/24'
    ]

SOURCERANGES_ABSENT = [
    '10.0.0.0/0',
    '192.168.1.0/24'
    ]

TARGETTAGS_PRESENT = [
    'http-server',
    'https-server'
    ]

TARGETTAGS_ABSENT = [
    'http-server',
    'https-server'
    ]


class FirewallTestCase(SecurityMonkeyTestCase):
    def test___port_range_exists(self):
        from security_monkey.auditors.gcp.gce.firewall import GCEFirewallRuleAuditor
        auditor = GCEFirewallRuleAuditor(accounts=['unittest'])
        actual = auditor._port_range_exists(ALLOWED_LIST_WITH_PORTRANGE)
        self.assertTrue(isinstance(actual, list))

        actual = auditor._port_range_exists(ALLOWED_LIST_NO_PORTRANGE)
        self.assertFalse(actual)

    def test__target_tags_valid(self):
        from security_monkey.auditors.gcp.gce.firewall import GCEFirewallRuleAuditor
        auditor = GCEFirewallRuleAuditor(accounts=['unittest'])

        actual = auditor._target_tags_valid(TARGETTAGS_PRESENT)
        self.assertTrue(isinstance(actual, list))

        actual = auditor._target_tags_valid(TARGETTAGS_ABSENT)
        self.assertFalse(actual)

    def test__source_ranges_open(self):
        from security_monkey.auditors.gcp.gce.firewall import GCEFirewallRuleAuditor
        auditor = GCEFirewallRuleAuditor(accounts=['unittest'])
        
        actual = auditor._source_ranges_open(SOURCERANGES_PRESENT)
        self.assertTrue(isinstance(actual, list))

        actual = auditor._source_ranges_open(SOURCERANGES_ABSENT)
        self.assertFalse(actual)
