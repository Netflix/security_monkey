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
.. module: security_monkey.auditors.kms
    :platform: Unix

.. version:: $$VERSION$$
.. moduleauthor::  Alex Cline <alex.cline@gmail.com> @alex.cline

"""
from security_monkey.auditor import Auditor
from security_monkey.watchers.kms import KMS
import json

class KMSAuditor(Auditor):
    index = KMS.index
    i_am_singular = KMS.i_am_singular
    i_am_plural = KMS.i_am_plural

    def __init__(self, accounts=None, debug=False):
        super(KMSAuditor, self).__init__(accounts=accounts, debug=debug)

    def check_for_kms_policy_with_foreign_account(self, kms_item):
        """
        alert when a KMS master key contains a policy giving permissions
        to a foreign account
        """
        tag = '{0} contains policies with foreign account permissions.'.format(self.i_am_singular)
        key_account_id = kms_item.config.get("AWSAccountId")
        key_policies = kms_item.config.get("Policies")

        has_issue = False
        bad_statements = []

        for policy in key_policies:
            for statement in policy.get("Statement"):
                if statement and statement.get("Principal"):
                    aws_principal = statement.get("Principal").get("AWS")
                    # A principal can either be a single ARN in a string, or an array of ARNs
                    if isinstance(aws_principal, basestring):
                        aws_principal = [aws_principal]

                    print aws_principal
                    for arn in aws_principal:
                        if arn == "*":
                            has_issue = True
                            bad_statements.append(json.dumps(statement))
                            continue

                        statement_account_id = arn.split(":")[4]
                        if statement_account_id != key_account_id:
                            has_issue = True
                            bad_statements.append(json.dumps(statement))

        if has_issue:
            notes = ", ".join(bad_statements)
            self.add_issue(5, tag, kms_item, notes=notes)

