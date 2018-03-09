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
.. module: security_monkey.auditors.gcp.util
    :platform: Unix

.. version:: $$VERSION$$
.. moduleauthor::  Tom Melendez <supertom@google.com> @supertom

"""
from security_monkey.common.gcp.error import AuditIssue


def _gen_error_code(cat, subcat, prefix, postfix=None):
        s = "%s_%s_%s" % (str(cat).upper(),
                          str(prefix).upper(),
                          str(subcat).upper())
        if postfix:
            s += '_' + str(postfix).upper()
        return s


def make_audit_issue(cat, subcat, prefix, postfix=None, notes=None):
    ec = _gen_error_code(
        cat, subcat, prefix, postfix)
    return AuditIssue(code=ec, notes=notes)


def process_issues(auditor, ok, issues, item):
    if not ok:
        for issue in issues:
            sev = auditor.gcp_config.ISSUE_MAP[issue.code]['score']
            msg = auditor.gcp_config.ISSUE_MAP[issue.code]['msg']
            notes = None
            if issue.notes:
                notes = issue.notes
            auditor.add_issue(sev, msg, item, notes)
    return True

