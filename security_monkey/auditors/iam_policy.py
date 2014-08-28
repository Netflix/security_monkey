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

    explicit_iam_checks = [
        "iam:*",
        "iam:passrole"
    ]

    def __init__(self, accounts=None, debug=False):
        super(IAMPolicyAuditor, self).__init__(accounts=accounts, debug=debug)

    def _iterate_over_statements(self, sub_policies, check_statement_func):
        """
        For each Statement in the policy document, execute check_statement_func.
        Helps when you don't know if the Statement is going to be a list of dicts
        or a single dict.
        """
        for sub_policy_name in sub_policies:
            sub_policy = sub_policies[sub_policy_name]
            if type(sub_policy['Statement']) is list:
                statements = sub_policy['Statement']
                for statement in statements:
                    check_statement_func(statement)
            else:
                check_statement_func(sub_policy['Statement'])

    def library_check_iamobj_has_star_privileges(self, iamobj_item, policies_key='userpolicies'):
        """
        alert when an IAM Object has a policy allowing '*'.
        """
        tag = '{0} has full admin privileges.'.format(self.i_am_singular)

        def check_statement(statement):
            if "Action" in statement and statement["Action"] == "*":
                if statement["Effect"] == "Allow":
                    self.add_issue(10, tag, iamobj_item, notes=json.dumps(statement))

        self._iterate_over_statements(iamobj_item.config.get(policies_key, {}), check_statement)

    def library_check_iamobj_has_iam_star_privileges(self, iamobj_item, policies_key='userpolicies'):
        """
        alert when an IAM Object has a policy allowing 'iam:*'.
        """
        tag = '{0} has full IAM privileges.'.format(self.i_am_singular)

        def check_statement(statement):
            if statement["Effect"] == "Allow":
                if "Action" in statement and type(statement["Action"]) is list:
                    for action in statement["Action"]:
                        if action.lower() == "iam:*":
                            self.add_issue(10, tag, iamobj_item, notes=json.dumps(statement))
                else:
                    if "Action" in statement and statement["Action"].lower() == "iam:*":
                        self.add_issue(10, tag, iamobj_item, notes=json.dumps(statement))

        self._iterate_over_statements(iamobj_item.config.get(policies_key, {}), check_statement)

    def library_check_iamobj_has_iam_privileges(self, iamobj_item, policies_key='userpolicies'):
        """
        alert when an IAM Object has a policy allowing 'iam:XxxxxXxxx'.
        """
        tag = '{0} has IAM privileges.'.format(self.i_am_singular)

        def check_statement(statement):
            if statement["Effect"] == "Allow":
                if "Action" in statement and type(statement["Action"]) is list:
                    for action in statement["Action"]:
                        if action.lower().startswith("iam:") and action.lower() not in self.explicit_iam_checks:
                            self.add_issue(9, tag, iamobj_item, notes=json.dumps(statement))
                else:
                    if "Action" in statement and statement["Action"].lower().startswith("iam:") and statement["Action"].lower() not in self.explicit_iam_checks:
                        self.add_issue(9, tag, iamobj_item, notes=json.dumps(statement))

        self._iterate_over_statements(iamobj_item.config.get(policies_key, {}), check_statement)

    def library_check_iamobj_has_iam_passrole(self, iamobj_item, policies_key='userpolicies'):
        """
        alert when an IAM Object has a policy allowing 'iam:PassRole'.
        This allows the object to pass any role specified in the resource block to an ec2 instance.
        """
        tag = '{0} has iam:PassRole privileges.'.format(self.i_am_singular)

        def check_statement(statement):
            if statement["Effect"] == "Allow":
                if "Action" in statement and type(statement["Action"]) is list:
                    for action in statement["Action"]:
                        if action.lower() == "iam:passrole":
                            self.add_issue(9, tag, iamobj_item, notes=json.dumps(statement))
                else:
                    if "Action" in statement and statement["Action"].lower() == "iam:passrole":
                        self.add_issue(9, tag, iamobj_item, notes=json.dumps(statement))

        self._iterate_over_statements(iamobj_item.config.get(policies_key, {}), check_statement)

    def library_check_iamobj_has_notaction(self, iamobj_item, policies_key='userpolicies'):
        """
        alert when an IAM Object has a policy containing 'NotAction'.
        NotAction combined with an "Effect": "Allow" often provides more privilege
        than is desired.
        """
        tag = '{0} contains NotAction.'.format(self.i_am_singular)

        def check_statement(statement):
            if statement["Effect"] == "Allow":
                if "NotAction" in statement:
                    self.add_issue(10, tag, iamobj_item, notes=json.dumps(statement["NotAction"]))

        self._iterate_over_statements(iamobj_item.config.get(policies_key, {}), check_statement)

    def library_check_iamobj_has_security_group_permissions(self, iamobj_item, policies_key='userpolicies'):
        """
        alert when an IAM Object has ec2:AuthorizeSecurityGroupEgress or ec2:AuthorizeSecurityGroupIngress.
        """
        tag = '{0} can change security groups.'.format(self.i_am_singular)

        def check_statement(statement):
            if statement["Effect"] == "Allow":
                if "Action" in statement and type(statement["Action"]) is list:
                    for action in statement["Action"]:
                        if action.lower() == "ec2:authorizesecuritygroupegress" or action.lower() == "ec2:authorizesecuritygroupingress":
                            self.add_issue(7, tag, iamobj_item, notes=action)
                else:
                    if "Action" in statement:
                        action = statement["Action"]
                        if action.lower() == "ec2:authorizesecuritygroupegress" or action.lower() == "ec2:authorizesecuritygroupingress":
                            self.add_issue(7, tag, iamobj_item, notes=action)

        self._iterate_over_statements(iamobj_item.config.get(policies_key, {}), check_statement)
