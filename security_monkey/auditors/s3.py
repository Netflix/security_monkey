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

import re


class S3Auditor(Auditor):
  index = S3.index
  i_am_singular = S3.i_am_singular
  i_am_plural = S3.i_am_plural

  def __init__(self, accounts=None, debug=False):
    super(S3Auditor, self).__init__(accounts=accounts, debug=debug)

  def check_acl(self, s3_item):
    accounts = Account.query.all()
    S3_ACCOUNT_NAMES = [account.s3_name for account in accounts if account.third_party == False]
    S3_THIRD_PARTY_ACCOUNTS = [account.s3_name for account in accounts if account.third_party == True]

    acl = s3_item.config.get('grants', {})
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
      elif user in S3_ACCOUNT_NAMES:
        message = "ACL - Friendly Account Access."
        notes = "{} {}".format(",".join(acl[user]), user)
        self.add_issue(0, message, s3_item, notes=notes)
      elif user in S3_THIRD_PARTY_ACCOUNTS:
        message = "ACL - Friendly Third Party Access."
        notes = "{} {}".format(",".join(acl[user]), user)
        self.add_issue(0, message, s3_item, notes=notes)
      else:
        message = "ACL - Unknown Cross Account Access."
        notes = "{} {}".format(",".join(acl[user]), user)
        self.add_issue(10, message, s3_item, notes=notes)

  def check_policy(self, s3_item):
    policy = s3_item.config.get('policy', {})
    statements = policy.get('Statement', {})
    complained = []
    for statement in statements:
      self.inspect_policy_allow_all(statement, s3_item)
      self.inspect_policy_cross_account(statement, s3_item, complained)
      self.inspect_policy_conditionals(statement, s3_item)

  def inspect_policy_allow_all(self, statement, s3_item):
    if statement['Effect'] == "Allow":
      if statement['Principal'] == "*":
        message = "POLICY - This Policy Allows Access From Anyone."
        self.add_issue(10, message, s3_item)
        return

      if 'AWS' in statement['Principal']:
        if statement['Principal']['AWS'] == "*":
          message = "POLICY - This Policy Allows Access From Anyone."
          self.add_issue(10, message, s3_item)
          return

  def inspect_policy_cross_account(self, statement, s3_item, complained):
    try:
      if 'Effect' in statement:
        effect = statement['Effect']
        if effect == 'Allow':
          if 'Principal' in statement:
            principal = statement["Principal"]
            if type(principal) is dict and 'AWS' in principal:
              aws_entries = principal["AWS"]
              if type(aws_entries) is str or type(aws_entries) is unicode:
                if aws_entries[0:26] not in complained:
                  self.processCrossAccount(aws_entries, s3_item)
                  complained.append(aws_entries[0:26])
              else:
                for aws_entry in aws_entries:
                  if aws_entry[0:26] not in complained:
                    self.processCrossAccount(aws_entry, s3_item)
                    complained.append(aws_entry[0:26])
    except Exception, e:
      print "Exception in cross_account. {} {}".format(Exception, e)
      import traceback
      print traceback.print_exc()

  def processCrossAccount(self, arn, s3_item):
    from security_monkey.constants import Constants
    m = re.match(r'arn:aws:iam::([0-9*]+):', arn)

    # BAD POLICY - Cross Account Access: Bad ARN: *
    # "Bad ARN: {}".format(arn)
    if not m:
      if not '*' == arn:
        print "Bad ARN: {}".format(arn)
      return

    # 'WILDCARD ARN: *'
    # This is caught by check_policy_allow_all(), so ignore here.
    if '*' == m.group(1):
      print "This is an odd arn: {}".format(arn)
      return

    # Friendly Account.
    if Constants.account_by_number(m.group(1)):
      message = "POLICY - Friendly Account Access."
      notes = "{}".format(Constants.account_by_number(m.group(1)))
      self.add_issue(0, message, s3_item, notes=notes)
      return

    # Friendly Third Party
    from security_monkey.constants import KNOWN_FRIENDLY_THIRDPARTY_ACCOUNTS
    if m.group(1) in KNOWN_FRIENDLY_THIRDPARTY_ACCOUNTS:
      message = "POLICY - Friendly Third Party Account Access."
      notes = "{}".format(KNOWN_FRIENDLY_THIRDPARTY_ACCOUNTS[m.group(1)])
      self.add_issue(0, message, s3_item, notes=notes)
      return

    # Foreign Unknown Account
    message = "POLICY - Unknown Cross Account Access."
    notes = "Account ID: {} ARN: {}".format(m.group(1), arn)
    self.add_issue(10, message, s3_item, notes=notes)
    return

  def inspect_policy_conditionals(self, statement, s3_item):
    if 'Condition' in statement:
      message = "POLICY - This policy has conditions."
      self.add_issue(3, message, s3_item)
