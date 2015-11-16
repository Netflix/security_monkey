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
.. module: security_monkey.auditors.sns
    :platform: Unix

.. version:: $$VERSION$$
.. moduleauthor:: Patrick Kelley <pkelley@netflix.com> @monkeysecurity

"""

from security_monkey.common.arn import ARN
from security_monkey.auditor import Auditor
from security_monkey.watchers.sns import SNS
from security_monkey.exceptions import InvalidARN
from security_monkey.exceptions import InvalidSourceOwner
from security_monkey.datastore import Account

import re


class SNSAuditor(Auditor):
    index = SNS.index
    i_am_singular = SNS.i_am_singular
    i_am_plural = SNS.i_am_plural

    def __init__(self, accounts=None, debug=False):
        super(SNSAuditor, self).__init__(accounts=accounts, debug=debug)

    def check_snstopicpolicy_empty(self, snsitem):
        """
        alert on empty SNS Policy
        """
        tag = "SNS Topic Policy is empty"
        severity = 1
        if snsitem.config.get('policy', {}) == {}:
            self.add_issue(severity, tag, snsitem, notes=None)

    def check_subscriptions_crossaccount(self, snsitem):
        """
        "subscriptions": [
          {
               "Owner": "020202020202",
               "Endpoint": "someemail@example.com",
               "Protocol": "email",
               "TopicArn": "arn:aws:sns:us-east-1:020202020202:somesnstopic",
               "SubscriptionArn": "arn:aws:sns:us-east-1:020202020202:somesnstopic:..."
          }
        ]
        """
        subscriptions = snsitem.config.get('subscriptions', [])
        for subscription in subscriptions:
            source = '{0} subscription to {1}'.format(
                subscription.get('Protocol', None),
                subscription.get('Endpoint', None)
            )
            owner = subscription.get('Owner', None)
            self._check_cross_account(owner, snsitem, source)

    def _parse_arn(self, arn_input, account_numbers, snsitem):
        if arn_input == '*':
            notes = "An SNS policy where { 'Principal': { 'AWS': '*' } } must also have"
            notes += " a {'Condition': {'StringEquals': { 'AWS:SourceOwner': '<ARN>' } } }"
            notes += " or it is open to the world."
            self.add_issue(10, 'SNS Topic open to everyone', snsitem, notes=notes)
            return

        arn = ARN(arn_input)
        if arn.error:
            self.add_issue(3, 'Auditor could not parse ARN', snsitem, notes=arn_input)
            return

        if arn.tech == 's3':
            notes = "SNS allows access from S3 bucket [{}]. ".format(arn.name)
            notes += "Security Monkey does not yet have the capability to determine if this is "
            notes += "a friendly S3 bucket.  Please verify manually."
            self.add_issue(3, 'SNS allows access from S3 bucket', snsitem, notes=notes)
        else:
            account_numbers.append(arn.account_number)

    def check_snstopicpolicy_crossaccount(self, snsitem):
        """
        alert on cross account access
        """
        policy = snsitem.config.get('policy', {})
        for statement in policy.get("Statement", []):
            account_numbers = []
            princ = statement.get("Principal", {})
            if isinstance(princ, dict):
                princ_aws = princ.get("AWS", "error")
            else:
                princ_aws = princ

            if princ_aws == "*":
                condition = statement.get('Condition', {})
                arns = ARN.extract_arns_from_statement_condition(condition)

                if not arns:
                    tag = "SNS Topic open to everyone"
                    notes = "An SNS policy where { 'Principal': { 'AWS': '*' } } must also have"
                    notes += " a {'Condition': {'StringEquals': { 'AWS:SourceOwner': '<ARN>' } } }"
                    notes += " or it is open to the world. In this case, anyone is allowed to perform "
                    notes += " this action(s): {}".format(statement.get("Action"))
                    self.add_issue(10, tag, snsitem, notes=notes)

                for arn in arns:
                    self._parse_arn(arn, account_numbers, snsitem)

            else:
                if isinstance(princ_aws, list):
                    for entry in princ_aws:
                        arn = ARN(entry)
                        if arn.error:
                            self.add_issue(3, 'Auditor could not parse ARN', snsitem, notes=entry)
                            continue

                        account_numbers.append(arn.account_number)
                else:
                    arn = ARN(princ_aws)
                    if arn.error:
                        self.add_issue(3, 'Auditor could not parse ARN', snsitem, notes=princ_aws)
                    else:
                        account_numbers.append(arn.account_number)

            for account_number in account_numbers:
                self._check_cross_account(account_number, snsitem, 'policy')
