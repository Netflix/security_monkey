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
.. module: security_monkey.auditors.iam_policy
    :platform: Unix

.. version:: $$VERSION$$
.. moduleauthor::  Patrick Kelley <pkelley@netflix.com> @monkeysecurity

"""
from security_monkey.auditor import Auditor

import json


class IAMPolicyAuditor(Auditor):

  def __init__(self, accounts=None, debug=False):
    super(IAMPolicyAuditor, self).__init__(accounts=accounts, debug=debug)

  def library_check_iamobj_has_star_privileges(self, iamobj_item, policies_key='userpolicies'):
      """
      alert when an IAM Object has a policy allowing '*'.
      """
      def check_statement(statement):
        if "Action" in statement and statement["Action"] == "*":
          if statement["Effect"] == "Allow":
            self.add_issue(10, tag, iamobj_item, notes=json.dumps(statement))

      tag = '{0} has full admin privileges.'.format(self.i_am_singular)
      sub_policies = iamobj_item.config.get(policies_key, {})
      for sub_policy_name in sub_policies:
        sub_policy = sub_policies[sub_policy_name]
        if type(sub_policy['Statement']) is list:
          statements = sub_policy['Statement']
          for statement in statements:
            check_statement(statement)
        else:
          check_statement(sub_policy['Statement'])

  def library_check_iamobj_has_iam_star_privileges(self, iamobj_item, policies_key='userpolicies'):
      """
      alert when an IAM Object has a policy allowing 'iam:*'.
      """
      def check_statement(statement):
        if statement["Effect"] == "Allow":
          if "Action" in statement and type(statement["Action"]) is list:
            for action in statement["Action"]:
              if action == "iam:*":
                self.add_issue(10, tag, iamobj_item, notes=json.dumps(statement))
          else:
            if "Action" in statement and statement["Action"] == "iam:*":
              self.add_issue(10, tag, iamobj_item, notes=json.dumps(statement))

      sub_policies = iamobj_item.config.get(policies_key, {})
      tag = '{0} has full IAM privileges.'.format(self.i_am_singular)
      for sub_policy_name in sub_policies:
        sub_policy = sub_policies[sub_policy_name]
        if type(sub_policy['Statement']) is list:
          statements = sub_policy['Statement']
          for statement in statements:
            check_statement(statement)
        else:
          check_statement(sub_policy['Statement'])

  def library_check_iamobj_has_iam_privileges(self, iamobj_item, policies_key='userpolicies'):
      """
      alert when an IAM Object has a policy allowing 'iam:XxxxxXxxx'.
      """
      def check_statement(statement):
        if statement["Effect"] == "Allow":
          if "Action" in statement and type(statement["Action"]) is list:
            for action in statement["Action"]:
              if action.startswith("iam:") and action != "iam:*":
                self.add_issue(9, tag, iamobj_item, notes=json.dumps(statement))
          else:
            if "Action" in statement and statement["Action"].startswith("iam:") and statement["Action"] != "iam:*":
              self.add_issue(9, tag, iamobj_item, notes=json.dumps(statement))

      sub_policies = iamobj_item.config.get(policies_key, {})
      tag = '{0} has IAM privileges.'.format(self.i_am_singular)
      for sub_policy_name in sub_policies:
        sub_policy = sub_policies[sub_policy_name]
        if type(sub_policy['Statement']) is list:
          statements = sub_policy['Statement']
          for statement in statements:
            check_statement(statement)
        else:
          check_statement(sub_policy['Statement'])
