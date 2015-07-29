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

from security_monkey.auditor import Auditor
from security_monkey.watchers.sqs import SQS
from security_monkey.exceptions import InvalidARN
from security_monkey.exceptions import InvalidSourceOwner
from security_monkey.datastore import Account

import re


class SQSAuditor(Auditor):
    index = SQS.index
    i_am_singular = SQS.i_am_singular
    i_am_plural = SQS.i_am_plural

    def __init__(self, accounts=None, debug=False):
        super(SQSAuditor, self).__init__(accounts=accounts, debug=debug)

    def check_sqstopicpolicy_crossaccount(self, sqsitem):
        """
        alert on cross account access
        """
        policy = sqsitem.config
        for statement in policy.get("Statement", []):
            account_numbers = []
            account_number = ''
            princ = statement.get("Principal", {})
            if isinstance(princ, dict):
                princ_aws = princ.get("AWS", "error")
            else:
                princ_aws = princ
            if princ_aws == "*":
                topic_arn = statement.get("Condition", {}) \
                    .get("ArnEquals", {}) \
                    .get("AWS:SourceArn", None)
                if not topic_arn:
                    tag = "SQS Topic open to everyone"
                    notes = "An SQS policy where { 'Principal': { 'AWS': '*' } } must also have"
                    notes += " a {'Condition': {'ArnEquals': { 'AWS:SourceArn': '<ACCOUNT_NUMBER>' } } }"
                    notes += " or it is open to the world. In this case, anyone is allowed to perform "
                    notes += " this action(s): {}".format(statement.get("Action"))
                    self.add_issue(10, tag, sqsitem, notes=notes)
                    continue
                else:

                    try:
                        account_numbers.append(str(re.search('arn:aws:sns:[a-z-]+-\d:([0-9-]+):', topic_arn).group(1)))
                    except:
                        raise InvalidARN(topic_arn)

            else:
                if isinstance(princ_aws, list):
                    for entry in princ_aws:
                        account_numbers.append(str(entry))
                else:
                    try:
                        account_numbers.append(str(princ_aws))
                    except:
                        raise InvalidSourceOwner(princ_aws)

            for account_number in account_numbers:
                self._check_account(account_number, sqsitem, 'policy')
                
    def _check_account(self, account_number, sqsitem, source):
        account = Account.query.filter(Account.number == account_number).first()
        account_name = None
        if account is not None:
            account_name = account.name

        src = account_name
        dst = sqsitem.account

        if src == dst:
            return None

        notes = "SRC [{}] DST [{}]. Location: {}".format(src, dst, source)

        if not account_name:
            tag = "Unknown Cross Account Access"
            self.add_issue(10, tag, sqsitem, notes=notes)
        elif account_name != sqsitem.account and not account.third_party:
            tag = "Friendly Cross Account Access"
            self.add_issue(0, tag, sqsitem, notes=notes)
        elif account_name != sqsitem.account and account.third_party:
            tag = "Friendly Third Party Cross Account Access"
            self.add_issue(0, tag, sqsitem, notes=notes)