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


def extract_condition_account_numbers(condition):
    condition_subsection = condition.get('StringLike', {}) or \
        condition.get('ForAllValues:StringLike', {}) or \
        condition.get('ForAnyValue:StringLike', {}) or \
        condition.get('StringEquals', {}) or \
        condition.get('ForAllValues:StringEquals', {}) or \
        condition.get('ForAnyValue:StringEquals', {})
    
    condition_accounts = []
    for key, value in condition_subsection.iteritems():
        if key.lower() == 'kms:calleraccount':
            if isinstance(value, list):
                condition_accounts.extend(value)
            else:
                condition_accounts.append(value)
    
    return condition_accounts


class KMSAuditor(Auditor):
    index = KMS.index
    i_am_singular = KMS.i_am_singular
    i_am_plural = KMS.i_am_plural

    def __init__(self, accounts=None, debug=False):
        super(KMSAuditor, self).__init__(accounts=accounts, debug=debug)

    def check_for_kms_key_rotation(self, kms_item):
        """
        Alert when a KMS key is not configured for rotation
        This is a AWS CIS Foundations Benchmark audit item (2.8)
        """
        rotation_status = kms_item.config.get('KeyRotationEnabled')
        if not rotation_status:
            self.add_issue(1, 'KMS key is not configured for rotation.', kms_item)

    def check_for_kms_policy_with_foreign_account(self, kms_item):
        """
        alert when a KMS master key contains a policy giving permissions
        to a foreign account
        """
        tag = '{0} contains policies with foreign account permissions.'.format(self.i_am_singular)
        key_account_id = kms_item.config.get("AWSAccountId")
        key_policies = kms_item.config.get("Policies")

        for policy in key_policies:
            for statement in policy.get("Statement"):
                condition_accounts = []
                if 'Condition' in statement:
                    condition = statement.get('Condition')
                    if condition:
                        condition_accounts = extract_condition_account_numbers(condition)

                    cross_accounts = [account for account in condition_accounts if account != key_account_id]
                    if cross_accounts:
                        notes = "Condition - kms:CallerAccount: {}".format(json.dumps(cross_accounts))
                        self.add_issue(5, tag, kms_item, notes=notes)

                if statement and statement.get("Principal"):
                    aws_principal = statement.get("Principal")
                    if isinstance(aws_principal, dict):
                        if 'AWS' in aws_principal:
                            aws_principal = aws_principal.get("AWS")
                        elif 'Service' in aws_principal:
                            aws_principal = aws_principal.get("Service")

                    if isinstance(aws_principal, basestring):
                        # Handles the case where the prnciple is *
                        aws_principal = [aws_principal]

                    principal_account_ids = set()
                    for arn in aws_principal:
                        if arn == "*" and not condition_accounts and "allow" == statement.get('Effect').lower():
                            notes = "An KMS policy where { 'Principal': { 'AWS': '*' } } must also have"
                            notes += " a {'Condition': {'StringEquals': { 'kms:CallerAccount': '<AccountNumber>' } } }"
                            notes += " or it is open to the world."
                            self.add_issue(5, tag, kms_item, notes=notes)
                            continue

                        if ':' not in arn:
                            # can happen if role is deleted
                            # and ARN is replaced wih role id.
                            continue

                        statement_account_id = arn.split(":")[4]
                        if statement_account_id != key_account_id:
                            principal_account_ids.add(statement_account_id)

                    if principal_account_ids:
                        notes = "Principal - {}".format(json.dumps(sorted(list(principal_account_ids))))
                        self.add_issue(5, tag, kms_item, notes=notes)
