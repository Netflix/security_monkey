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
.. module: security_monkey.auditors.gcp.gcs.bucket
    :platform: Unix

.. version:: $$VERSION$$
.. moduleauthor::  Tom Melendez <supertom@google.com> @supertom

"""
from security_monkey.auditor import Auditor
from security_monkey.auditors.gcp.util import make_audit_issue, process_issues
from security_monkey.common.gcp.config import AuditorConfig
from security_monkey.common.gcp.error import AuditIssue
from security_monkey.watchers.gcp.gcs.bucket import GCSBucket

# NOTE: issue scores and messages are defined in
# security_monkey/common/gcp/config.py


class GCSBucketAuditor(Auditor):
    index = GCSBucket.index
    i_am_singular = GCSBucket.i_am_singular
    i_am_plural = GCSBucket.i_am_plural
    gcp_config = AuditorConfig.GCSBucket

    def __init__(self, accounts=None, debug=True):
        super(GCSBucketAuditor, self).__init__(accounts=accounts, debug=debug)

    def _acl_allusers_exists(self, acl_list, error_cat='ACL'):
        """
        Looks for allUsers in acl.

        return: [list of AuditIssues]
        """
        allusers = 'allUsers'
        errors = []
        for acl in acl_list:
            entity = acl.get('entity')
            role = acl.get('role')
            if entity == allusers:
                # TODO(supertom): notes
                ae = make_audit_issue(error_cat, 'ROLE', allusers, role)
                errors.append(ae)
        return errors

    def _acl_max_owners(self, acl_list, error_cat='ACL'):
        """
        Looks for Max OWNERS in acl.

        return: [list of AuditIssues]
        """
        errors = []
        if self.gcp_config.MAX_OWNERS_PER_BUCKET:
            owner = 'OWNER'
            count = 0
            for acl in acl_list:
                role = acl.get('role')
                if role == owner:
                    count += 1
                    if count > self.gcp_config.MAX_OWNERS_PER_BUCKET:
                        ae = make_audit_issue(
                            error_cat, 'MAX', owner)
                        errors.append(ae)
        return errors

    def _cors_method(self, cors_list, error_cat='CORS'):
        """
        Looks at the CORS method. Anything other than GET is flagged.

        return: [list of AuditIssues]
        """
        errors = []
        for cors in cors_list:
            methods = cors.get('method')
            for method in methods:
                if method == '*':
                    method = 'ALL'
                if method != 'GET':
                    ae = make_audit_issue(
                        error_cat, 'METHOD', method)
                    errors.append(ae)
        return errors

    def inspect_acl(self, item):
        """
        Driver for Bucket ACL. Calls helpers as needed.

        return: (bool, [list of AuditIssues])
        """
        acl = item.config.get('Acl')
        errors_acl = []
        if acl:
            err = self._acl_allusers_exists(acl, 'ACL')
            errors_acl.extend(err) if err else None

            err = self._acl_max_owners(acl, 'ACL')
            errors_acl.extend(err) if err else None
            if errors_acl:
                return (False, errors_acl)
            return (True, None)
        else:
            return (False, [make_audit_issue("ACL", 'FOUND', "NOT")])

    def inspect_default_object_acl(self, item):
        """
        Driver for Default Object ACL. Calls helpers as needed.

        return: (bool, [list of AuditIssues])
        """
        def_obj_acl = item.config.get('DefaultObjectAcl')
        errors_acl = []
        if def_obj_acl:
            err = self._acl_allusers_exists(def_obj_acl, 'DEFAULT_OBJECT_ACL')
            errors_acl.extend(err) if err else None

            err = self._acl_max_owners(def_obj_acl, 'DEFAULT_OBJECT_ACL')
            errors_acl.extend(err) if err else None
            if errors_acl:
                return (False, errors_acl)
            return (True, None)
        else:
            return (False, [make_audit_issue("DEFAULT_OBJECT_ACL", 'FOUND', "NOT")])

    def inspect_cors(self, item):
        """
        Driver for CORS field. Calls helpers as needed.

        return: (bool, [list of AuditIssues])
        """
        cors = item.config.get('Cors')
        if cors:
            errors = []
            err = self._cors_method(cors)
            errors.extend(err) if err else None
            if errors:
                return (False, errors)
        return (True, None)

    def check_cors(self, item):
        """
        Check CORS field.
        CORS policy is set with: gsutil cors set /tmp/cors.json gs://your-bucket
        """
        (ok, errors) = self.inspect_cors(item)
        process_issues(self, ok, errors, item)

    def check_acl(self, item):
        (ok, errors) = self.inspect_acl(item)
        process_issues(self, ok, errors, item)

    def check_default_object_acl(self, item):
        (ok, errors) = self.inspect_default_object_acl(item)
        process_issues(self, ok, errors, item)
