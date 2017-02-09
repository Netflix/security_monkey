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
.. module: security_monkey.auditors.gcp.gce_iam
    :platform: Unix

.. version:: $$VERSION$$
.. moduleauthor::  Tom Melendez <supertom@google.com> @supertom

"""

from security_monkey.auditor import Auditor
from security_monkey.auditors.gcp.util import make_audit_issue, process_issues
from security_monkey.common.gcp.config import AuditorConfig
from security_monkey.common.gcp.error import AuditIssue
from security_monkey.watchers.gcp.iam.serviceaccount import IAMServiceAccount

# NOTE: issue scores and messages are defined in
# security_monkey/common/gcp/config.py


class IAMServiceAccountAuditor(Auditor):
    index = IAMServiceAccount.index
    i_am_singular = IAMServiceAccount.i_am_singular
    i_am_plural = IAMServiceAccount.i_am_plural
    gcp_config = AuditorConfig.IAMServiceAccount

    def __init__(self, accounts=None, debug=True):
        super(
            IAMServiceAccountAuditor,
            self).__init__(
            accounts=accounts,
            debug=debug)

    def _max_keys(self, key_count, error_cat='SA'):
        """
        Alert when a service account has too many keys.

        return: [list of AuditIssues]
        """
        errors = []
        if key_count > self.gcp_config.MAX_SERVICEACCOUNT_KEYS:
            ae = make_audit_issue(
                error_cat, 'MAX', 'KEYS')
            ae.notes = 'Too Many Keys (count: %s, max: %s)' % (
                key_count, self.gcp_config.MAX_SERVICEACCOUNT_KEYS)
            errors.append(ae)
        return errors

    def _actor_role(self, policies, error_cat='SA'):
        """
        Determine if a serviceaccount actor is specified.

        return: [list of AuditIssues]
        """
        errors = []
        for policy in policies:
            role = policy.get('Role')
            if role and role == 'iam.serviceAccountActor':
                ae = make_audit_issue(
                    error_cat, 'POLICY', 'ROLE', 'ACTOR')
                errors.append(ae)
        return errors

    def inspect_serviceaccount(self, item):
        """
        Driver for ServiceAccount. Calls helpers as needed.

        return: (bool, [list of AuditIssues])
        """
        errors = []

        err = self._max_keys(item.config.get('keys'))
        errors.extend(err) if err else None

        policies = item.config.get('policy')
        if policies:
            err = self._actor_role(policies)
            errors.extend(err) if err else None

        if errors:
            return (False, errors)
        return (True, None)

    def check_serviceaccount(self, item):
        (ok, errors) = self.inspect_serviceaccount(item)
        process_issues(self, ok, errors, item)
