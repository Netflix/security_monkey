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
"""
.. module: security_monkey.auditors.gcp.gce.network
    :platform: Unix

.. version:: $$VERSION$$
.. moduleauthor::  Tom Melendez <supertom@google.com> @supertom

"""
from security_monkey.auditor import Auditor
from security_monkey.auditors.gcp.util import make_audit_issue, process_issues
from security_monkey.common.gcp.config import AuditorConfig
from security_monkey.watchers.gcp.gce.network import GCENetwork

# NOTE: issue scores and messages are defined in
# security_monkey/common/gcp/config.py


class GCENetworkAuditor(Auditor):
    index = GCENetwork.index
    i_am_singular = GCENetwork.i_am_singular
    i_am_plural = GCENetwork.i_am_plural
    gcp_config = AuditorConfig.GCENetwork

    def __init__(self, accounts=None, debug=True):
        super(GCENetworkAuditor, self).__init__(accounts=accounts, debug=debug)

    def _legacy_exists(self, network, error_cat='NET'):
        """
        Look for legacy-style (non-subnetwork style) network.

        return: [list of AuditIssues]
        """
        errors = []
        subnetworks = network.get('Subnetworks', None)
        auto_create_subnetworks = network.get(
            'AutoCreateSubnetworks', None)

        # A network is considered 'legacy' if 'Subnetworks' AND 'AutoCreateSubnetworks'
        # do not exist in the dictionary.
        if subnetworks is None and auto_create_subnetworks is None:
            ae = make_audit_issue(
                error_cat, 'EXISTS', 'LEGACY')
            errors.append(ae)
        return errors

    def inspect_network(self, item):
        """
        Driver for Network. Calls helpers as needed.

        return: (bool, [list of AuditIssues])
        """
        errors = []
        network = item.config
        err = self._legacy_exists(network)
        errors.extend(err) if err else None

        if errors:
            return (False, errors)
        return (True, None)

    def check_networks(self, item):
        (ok, errors) = self.inspect_network(item)
        process_issues(self, ok, errors, item)
