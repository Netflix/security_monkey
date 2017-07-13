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
.. module: security_monkey.auditors.s3
    :platform: Unix

.. version:: $$VERSION$$
.. moduleauthor:: Patrick Kelley <pkelley@netflix.com> @monkeysecurity

"""

from security_monkey.auditor import Auditor
from security_monkey.watchers.s3 import S3
from security_monkey.datastore import Account


class S3Auditor(Auditor):
    index = S3.index
    i_am_singular = S3.i_am_singular
    i_am_plural = S3.i_am_plural

    def __init__(self, accounts=None, debug=False):
        super(S3Auditor, self).__init__(accounts=accounts, debug=debug)

    def check_acl(self, s3_item):
        accounts = Account.query.all()
        S3_ACCOUNT_NAMES = [account.getCustom("s3_name").lower() for account in accounts if not account.third_party and account.getCustom("s3_name")]
        S3_CANONICAL_IDS = [account.getCustom("canonical_id").lower() for account in accounts if not account.third_party and account.getCustom("canonical_id")]
        S3_THIRD_PARTY_ACCOUNTS = [account.getCustom("s3_name").lower() for account in accounts if account.third_party and account.getCustom("s3_name")]
        S3_THIRD_PARTY_ACCOUNT_CANONICAL_IDS = [account.getCustom("canonical_id").lower() for account in accounts if account.third_party and account.getCustom("canonical_id")]

        # Get the owner ID:
        owner = s3_item.config["Owner"]["ID"].lower()

        acl = s3_item.config.get('Grants', {})
        for user in acl.keys():
            if user == 'http://acs.amazonaws.com/groups/global/AuthenticatedUsers':
                message = "ACL - AuthenticatedUsers USED. "
                notes = "{}".format(",".join(acl[user]))
                self.add_issue(10, message, s3_item, notes=notes)
            elif user == 'http://acs.amazonaws.com/groups/global/AllUsers':
                message = "ACL - AllUsers USED."
                notes = "{}".format(",".join(acl[user]))
                self.add_issue(10, message, s3_item, notes=notes)
            elif user == 'http://acs.amazonaws.com/groups/s3/LogDelivery':
                message = "ACL - LogDelivery USED."
                notes = "{}".format(",".join(acl[user]))
                self.add_issue(0, message, s3_item, notes=notes)

            # DEPRECATED:
            elif user.lower() in S3_ACCOUNT_NAMES:
                message = "ACL - Friendly Account Access."
                notes = "{} {}".format(",".join(acl[user]), user)
                self.add_issue(0, message, s3_item, notes=notes)
            elif user.lower() in S3_THIRD_PARTY_ACCOUNTS:
                message = "ACL - Friendly Third Party Access."
                notes = "{} {}".format(",".join(acl[user]), user)
                self.add_issue(0, message, s3_item, notes=notes)

            elif user.lower() in S3_CANONICAL_IDS:
                # Owning account -- no issue
                if user.lower() == owner.lower():
                    continue

                message = "ACL - Friendly Account Access."
                notes = "{} {}".format(",".join(acl[user]), user)
                self.add_issue(0, message, s3_item, notes=notes)

            elif user.lower() in S3_THIRD_PARTY_ACCOUNT_CANONICAL_IDS:
                message = "ACL - Friendly Third Party Access."
                notes = "{} {}".format(",".join(acl[user]), user)
                self.add_issue(0, message, s3_item, notes=notes)

            else:
                message = "ACL - Unknown Cross Account Access."
                notes = "{} {}".format(",".join(acl[user]), user)
                self.add_issue(10, message, s3_item, notes=notes)

    def check_policy(self, s3_item):
        policy = s3_item.config.get('Policy', {})
        if not policy:
            message = "POLICY - No Policy."
            self.add_issue(0, message, s3_item)
            return

        statements = policy.get('Statement', {})
        complained = []
        for statement in statements:
            self.inspect_policy_allow_all(statement, s3_item)
            self.inspect_policy_cross_account(statement, s3_item, complained)

    def _condition_summary(self, statement):
        summary_values = set()
        try:
            for key in statement['Condition']:
                for subkey in statement['Condition'][key]:
                    summary_values.add('{k}/{s}'.format(k=key, s=subkey))
        except:
            pass
        return ', '.join(sorted(list(summary_values)))

    def inspect_policy_allow_all(self, statement, s3_item):
        
        if 'Condition' in statement:
            notes = self._condition_summary(statement)
            score = 3
            message = "POLICY - This Policy Allows Conditional Access From Anyone."
        else:
            notes = None
            score = 10
            message = "POLICY - This Policy Allows Access From Anyone."
        
        if statement.get('Effect') == "Allow":
            principal = statement.get('Principal')
            if isinstance(principal, basestring) and principal == "*":
                self.add_issue(score, message, s3_item, notes=notes)
                return

            if isinstance(principal, dict) and principal.get('AWS') == "*":
                self.add_issue(score, message, s3_item, notes=notes)
                return

    def inspect_policy_cross_account(self, statement, s3_item, complained):
        try:
            if statement.get('Effect') == 'Allow' and isinstance(statement.get("Principal"), dict):
                aws_entries = statement["Principal"].get("AWS", [])
                if isinstance(aws_entries, basestring):
                    aws_entries = [aws_entries]
                for aws_entry in aws_entries:
                    if aws_entry not in complained:
                        self.process_cross_account(aws_entry, s3_item)
                        complained.append(aws_entry)

        except Exception as e:
            print("Exception in cross_account. {} {}".format(Exception, e))
            import traceback
            print(traceback.print_exc())

    def process_cross_account(self, input, s3_item):
        from security_monkey.common.arn import ARN
        arn = ARN(input)

        if arn.error and input != input:
            message = "POLICY - Bad ARN"
            notes = "{}".format(arn)
            self.add_issue(3, message, s3_item, notes=notes)
            return

        # 'WILDCARD ARN: *'
        # This is caught by check_policy_allow_all(), so ignore here.
        if '*' == arn.account_number:
            print("This is an odd arn: {}".format(arn))
            return

        account = Account.query.filter(Account.identifier==arn.account_number).first()
        if account:
            # Friendly Account.
            if not account.third_party:
                message = "POLICY - Friendly Account Access."
                notes = "{}".format(account.name)
                self.add_issue(0, message, s3_item, notes=notes)
                return
            # Friendly Third Party
            else:
                message = "POLICY - Friendly Third Party Account Access."
                notes = "{}".format(account.name)
                self.add_issue(0, message, s3_item, notes=notes)
                return

        # Foreign Unknown Account
        message = "POLICY - Unknown Cross Account Access."
        notes = "Account ID: {} ARN: {}".format(arn.account_number, input)
        self.add_issue(10, message, s3_item, notes=notes)
        return
