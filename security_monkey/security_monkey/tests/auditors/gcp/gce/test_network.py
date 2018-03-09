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
.. module: security_monkey.tests.auditors.gcp.gce.test_network
    :platform: Unix

.. version:: $$VERSION$$
.. moduleauthor::  Tom Melendez <supertom@google.com> @supertom
"""

AUTO_NETWORK_DICT = {
    "AutoCreateSubnetworks": True,
    "CreationTimestamp": "2016-05-09T11:15:47.434-07:00",
    "Description": "Default network for the project",
    "Id": "5748637682906434876",
    "Kind": "compute#network",
    "Name": "default",
    "SelfLink": "https://www.googleapis.com/compute/v1/projects/my-project-one/global/networks/default",
    "Subnetworks": [
        {
            "CreationTimestamp": "2016-10-25T09:53:00.777-07:00",
            "GatewayAddress": "10.146.0.1",
            "Id": "1852214226435846915",
            "IpCidrRange": "10.146.0.0/20",
            "Kind": "compute#subnetwork",
            "Name": "default",
            "Network": "https://www.googleapis.com/compute/v1/projects/my-project-one/global/networks/default",
            "Region": "https://www.googleapis.com/compute/v1/projects/my-project-one/regions/asia-northeast1",
            "SelfLink": "https://www.googleapis.com/compute/v1/projects/my-project-one/regions/asia-northeast1/subnetworks/default"
        }
        
    ]
}

LEGACY_NETWORK = {
    "kind": "compute#network",
    "id": "6570954185952335682",
    "creationTimestamp": "2016-08-04T13:46:37.261-07:00",
    "name": "network-b",
    "IPv4Range": "10.0.0.0/8",
    "gatewayIPv4": "10.0.0.1",
    "selfLink": "https://www.googleapis.com/compute/v1/projects/supertom-graphite/global/networks/network-b"
}


class NetworkTestCase(SecurityMonkeyTestCase):
    def test__legacy_exists(self):
        from security_monkey.auditors.gcp.gce.network import GCENetworkAuditor
        auditor = GCENetworkAuditor(accounts=['unittest'])

        actual = auditor._legacy_exists(AUTO_NETWORK_DICT)
        self.assertFalse(actual)
        actual = auditor._legacy_exists(LEGACY_NETWORK)
        self.assertTrue(isinstance(actual, list))
