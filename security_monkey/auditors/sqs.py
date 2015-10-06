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
.. module: security_monkey.auditors.sqs
    :platform: Unix

.. version:: $$VERSION$$
.. moduleauthor:: Denver Janke <denverjanke@gmail.com>

"""

from security_monkey.common.arn import ARN
from security_monkey import app
from security_monkey.auditor import Auditor
from security_monkey.watchers.sqs import SQS
from security_monkey.exceptions import InvalidARN
from security_monkey.exceptions import InvalidSourceOwner

import re


class SQSAuditor(Auditor):
    index = SQS.index
    i_am_singular = SQS.i_am_singular
    i_am_plural = SQS.i_am_plural

    def __init__(self, accounts=None, debug=False):
        super(SQSAuditor, self).__init__(accounts=accounts, debug=debug)

    def _parse_arn(self, arn_input, account_numbers, sqsitem):
        arn = ARN(arn_input)
        if arn.error:
            self.add_issue(3, 'Auditor could not parse ARN', sqsitem, notes=arn_input)
            return

        if arn.tech == 's3':
            notes = "SQS allows access from S3 bucket [{}]. ".format(arn.name)
            notes += "Security Monkey does not yet have the capability to determine if this is "
            notes += "a friendly S3 bucket.  Please verify manually."
            self.add_issue(3, 'SQS allows access from S3 bucket', sqsitem, notes=notes)
        else:
            account_numbers.append(arn.account_number)

    def _extract_arns_from_condition(self, condition, statement, acccount_numbers, sqsitem):
        condition_subsection\
            = condition.get('ArnEquals', {}) or \
              condition.get('ForAllValues:ArnEquals', {}) or \
              condition.get('ForAnyValue:ArnEquals', {}) or \
              condition.get('ArnLike', {}) or \
              condition.get('ForAllValues:ArnLike', {}) or \
              condition.get('ForAnyValue:ArnLike', {}) or \
              condition.get('StringLike', {}) or \
              condition.get('ForAllValues:StringLike', {}) or \
              condition.get('ForAnyValue:StringLike', {}) or \
              condition.get('StringEquals', {}) or \
              condition.get('ForAllValues:StringEquals', {}) or \
              condition.get('ForAnyValue:StringEquals', {})

        # aws:sourcearn can be found with in lowercase or camelcase or other cases...
        queue_arn = next((v for k,v in
                          condition_subsection.items()
                          if k.lower() == 'aws:sourcearn'), None)

        if not queue_arn:
            tag = "SQS Queue open to everyone"
            notes = "An SQS policy where { 'Principal': { 'AWS': '*' } } must also have"
            notes += " a {'Condition': {'ArnEquals': { 'AWS:SourceArn': '<ARN>' } } }"
            notes += " or it is open to the world. In this case, anyone is allowed to perform "
            notes += " this action(s): {}".format(statement.get("Action"))
            self.add_issue(10, tag, sqsitem, notes=notes)
            return []

        if not isinstance(queue_arn, list):
            return [queue_arn]
        return queue_arn

    def check_sqsqueue_crossaccount(self, sqsitem):
        """
        alert on cross account access
        """
        policy = sqsitem.config
        for statement in policy.get("Statement", []):
            account_numbers = []
            princ = statement.get("Principal", {})
            if isinstance(princ, dict):
                princ_aws = princ.get("AWS", "error")
            else:
                princ_aws = princ

            if princ_aws == "*":
                condition = statement.get('Condition', {})
                arns = self._extract_arns_from_condition(condition, statement, account_numbers, sqsitem)
                for arn in arns:
                    self._parse_arn(arn, account_numbers, sqsitem)

            else:
                if isinstance(princ_aws, list):
                    for entry in princ_aws:
                        arn = ARN(entry)
                        if arn.error:
                            self.add_issue(3, 'Auditor could not parse ARN', sqsitem, notes=entry)
                            continue

                        account_numbers.append(arn.account_number)
                else:
                    arn = ARN(princ_aws)
                    if arn.error:
                        self.add_issue(3, 'Auditor could not parse ARN', sqsitem, notes=princ_aws)
                    else:
                        account_numbers.append(arn.account_number)

            for account_number in account_numbers:
                self._check_cross_account(account_number, sqsitem, 'policy')
