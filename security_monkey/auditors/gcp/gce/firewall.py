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
.. module: security_monkey.auditors.gcp.gce.firewall
    :platform: Unix

.. version:: $$VERSION$$
.. moduleauthor::  Tom Melendez <supertom@google.com> @supertom

"""
from security_monkey.auditor import Auditor
from security_monkey.auditors.gcp.util import make_audit_issue, process_issues
from security_monkey.common.gcp.config import AuditorConfig
from security_monkey.common.gcp.error import AuditIssue
from security_monkey.watchers.gcp.gce.firewall import GCEFirewallRule

# NOTE: issue scores and messages are defined in
# security_monkey/common/gcp/config.py


class GCEFirewallRuleAuditor(Auditor):
    index = GCEFirewallRule.index
    i_am_singular = GCEFirewallRule.i_am_singular
    i_am_plural = GCEFirewallRule.i_am_plural
    gcp_config = AuditorConfig.GCEFirewallRule

    def __init__(self, accounts=None, debug=True):
        super(
            GCEFirewallRuleAuditor,
            self).__init__(
            accounts=accounts,
            debug=debug)

    def _port_range_exists(self, allowed_list, error_cat='ALLOWED'):
        """
        Check to see if a port range exists in the allowed field.
        """
        errors = []
        if allowed_list:
            for allowed in allowed_list:
                ports = allowed.get('ports', None)
                if ports:
                    for port in ports:
                        if str(port).find('-') > -1:
                            ae = make_audit_issue(
                                error_cat, 'EXISTS', 'PORTRANGE')
                            ae.notes = '%s:%s' % (allowed['IPProtocol'], port)
                            errors.append(ae)
        return errors

    def _target_tags_valid(self, target_tags, error_cat='TARGET_TAGS'):
        """
        Check to see if target tags are present.
        """
        errors = []

        if not target_tags:
            ae = make_audit_issue(
                error_cat, 'FOUND', 'NOT')
            errors.append(ae)
        return errors

    def _source_ranges_open(self, source_ranges, error_cat='SOURCE_RANGES'):
        """
        Check to see if the source range field is set to allow all traffic
        """
        errors = []
        open_range = '0.0.0.0/0'
        for source_range in source_ranges:
            if source_range == open_range:
                ae = make_audit_issue(
                    error_cat, 'OPEN', 'TRAFFIC')
                errors.append(ae)
        return errors

    def inspect_target_tags(self, item):
        """
        Driver for Target Tags. Calls helpers as needed.

        return: (bool, [list of AuditIssues])
        """
        errors = []

        target_tags = item.config.get('TargetTags', None)
        err = self._target_tags_valid(target_tags)
        errors.extend(err) if err else None

        if errors:
            return (False, errors)
        return (True, None)

    def inspect_source_ranges(self, item):
        """
        Driver for Source Ranges. Calls helpers as needed.

        return: (bool, [list of AuditIssues])
        """
        errors = []

        source_ranges = item.config.get('SourceRanges', None)
        if source_ranges:
            err = self._source_ranges_open(source_ranges)
            errors.extend(err) if err else None

        if errors:
            return (False, errors)
        return (True, None)

    def inspect_allowed(self, item):
        """
        Driver for Allowed field (protocol/ports list). Calls helpers as needed.

        return: (bool, [list of AuditIssues])
        """
        errors = []

        err = self._port_range_exists(item.config.get('Allowed'))
        errors.extend(err) if err else None

        if errors:
            return (False, errors)
        return (True, None)

    def check_allowed(self, item):
        (ok, errors) = self.inspect_allowed(item)
        process_issues(self, ok, errors, item)

    def check_target_tags(self, item):
        (ok, errors) = self.inspect_target_tags(item)
        process_issues(self, ok, errors, item)

    def check_source_ranges(self, item):
        (ok, errors) = self.inspect_source_ranges(item)
        process_issues(self, ok, errors, item)
