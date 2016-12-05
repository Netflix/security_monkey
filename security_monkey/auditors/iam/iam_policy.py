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
.. module: security_monkey.auditors.iam.iam_policy
    :platform: Unix

.. version:: $$VERSION$$
.. moduleauthor::  Patrick Kelley <pkelley@netflix.com> @monkeysecurity

"""
from security_monkey.auditor import Auditor
from security_monkey.watchers.iam.managed_policy import ManagedPolicy
from security_monkey import app
import json


def _iterate_over_sub_policies(sub_policies, check_statement_func):
    """
    For each named policy in the policy document, call _iterate_over_statements.
    """
    for sub_policy_name in sub_policies:
        sub_policy = sub_policies[sub_policy_name]
        _iterate_over_statements(sub_policy, check_statement_func)


def _iterate_over_statements(sub_policy, check_statement_func):
    """
    For every statement in a given policy, execute check_statement_func.
    Helps when you don't know if the Statement is going to be a list of dicts
    or a single dict.

    :param sub_policy: A single named policy within an IAM object.
    :param check_statement_func: The function used to inspect an IAM Object
    :return: None
    """
    if type(sub_policy['Statement']) is list:
        statements = sub_policy['Statement']
        for statement in statements:
            check_statement_func(statement)
    else:
        check_statement_func(sub_policy['Statement'])


class IAMPolicyAuditor(Auditor):

    explicit_iam_checks = [
        "iam:*",
        "iam:passrole"
    ]

    def __init__(self, accounts=None, debug=False):
        super(IAMPolicyAuditor, self).__init__(accounts=accounts, debug=debug)

    def library_check_iamobj_has_star_privileges(self, iamobj_item, policies_key='InlinePolicies', multiple_policies=True):
        """
        alert when an IAM Object has a policy allowing '*'.
        """
        tag = '{0} has full admin privileges.'.format(self.i_am_singular)

        def check_statement(statement):
            if statement["Effect"] == "Allow":
                if "Action" in statement and type(statement["Action"]) is list:
                    for action in statement["Action"]:
                        if action == "*":
                            self.add_issue(10, tag, iamobj_item, notes=json.dumps(statement))
                else:
                    if "Action" in statement and statement["Action"] == "*":
                        self.add_issue(10, tag, iamobj_item, notes=json.dumps(statement))

        if multiple_policies:
            _iterate_over_sub_policies(iamobj_item.config.get(policies_key, {}), check_statement)
        else:
            _iterate_over_statements(iamobj_item.config[policies_key], check_statement)

    def library_check_iamobj_has_iam_star_privileges(self, iamobj_item, policies_key='InlinePolicies', multiple_policies=True):
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

        if multiple_policies:
            _iterate_over_sub_policies(iamobj_item.config.get(policies_key, {}), check_statement)
        else:
            _iterate_over_statements(iamobj_item.config[policies_key], check_statement)

    def library_check_iamobj_has_iam_privileges(self, iamobj_item, policies_key='InlinePolicies', multiple_policies=True):
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

        if multiple_policies:
            _iterate_over_sub_policies(iamobj_item.config.get(policies_key, {}), check_statement)
        else:
            _iterate_over_statements(iamobj_item.config[policies_key], check_statement)

    def library_check_iamobj_has_iam_passrole(self, iamobj_item, policies_key='InlinePolicies', multiple_policies=True):
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

        if multiple_policies:
            _iterate_over_sub_policies(iamobj_item.config.get(policies_key, {}), check_statement)
        else:
            _iterate_over_statements(iamobj_item.config[policies_key], check_statement)

    def library_check_iamobj_has_notaction(self, iamobj_item, policies_key='InlinePolicies', multiple_policies=True):
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

        if multiple_policies:
            _iterate_over_sub_policies(iamobj_item.config.get(policies_key, {}), check_statement)
        else:
            _iterate_over_statements(iamobj_item.config[policies_key], check_statement)

    def library_check_iamobj_has_security_group_permissions(self, iamobj_item, policies_key='InlinePolicies', multiple_policies=True):
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

        if multiple_policies:
            _iterate_over_sub_policies(iamobj_item.config.get(policies_key, {}), check_statement)
        else:
            _iterate_over_statements(iamobj_item.config[policies_key], check_statement)

    def library_check_attached_managed_policies(self, iam_item, iam_type):
        """
        alert when an IAM item (group, user or role) is attached to a managed policy with issues
        """
        mp_items = self.get_auditor_support_items(ManagedPolicy.index, iam_item.account)
        managed_policies = iam_item.config.get('managed_policies', iam_item.config.get('ManagedPolicies'))
        for item_mp in managed_policies or []:
            found = False
            item_mp_arn = item_mp.get('arn', item_mp.get('Arn'))
            for mp_item in mp_items or [] and not found:
                mp_arn = mp_item.config.get('arn', mp_item.config.get('Arn'))
                if mp_arn == item_mp_arn:
                    found = True
                    self.link_to_support_item_issues(iam_item, mp_item.db_item, None, "Found issue(s) in attached Managed Policy")

            if not found:
                app.logger.error("IAM Managed Policy defined but not found for {}-{}".format(iam_item.index, iam_item.name))
