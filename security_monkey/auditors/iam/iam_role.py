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
.. module: security_monkey.auditors.iam.iam_role
    :platform: Unix

.. version:: $$VERSION$$
.. moduleauthor::  Patrick Kelley <pkelley@netflix.com> @monkeysecurity

"""
import json

from security_monkey.watchers.iam.iam_role import IAMRole
from security_monkey.auditors.iam.iam_policy import IAMPolicyAuditor


class IAMRoleAuditor(IAMPolicyAuditor):
    index = IAMRole.index
    i_am_singular = IAMRole.i_am_singular
    i_am_plural = IAMRole.i_am_plural

    def __init__(self, accounts=None, debug=False):
        super(IAMRoleAuditor, self).__init__(accounts=accounts, debug=debug)

    def check_star_assume_role_policy(self, iamrole_item):
        """
        alert when an IAM Role has an assume_role_policy_document but using a star
        instead of limiting the assume to a specific IAM Role.
        """
        tag = "{0} allows assume-role from anyone".format(self.i_am_singular)

        def check_statement(statement):
            action = statement.get("Action", None)
            if action and action == "sts:AssumeRole":
                effect = statement.get("Effect", None)
                if effect and effect == "Allow":
                    principal = statement.get("Principal", None)
                    if not principal:
                        return
                    if type(principal) is dict:
                        aws = principal.get("AWS", None)
                        if aws and aws == "*":
                            self.add_issue(10, tag, iamrole_item,
                                           notes=json.dumps(statement))
                    elif aws and type(aws) is list:
                        for entry in aws:
                            if entry == "*":
                                self.add_issue(10, tag, iamrole_item,
                                               notes=json.dumps(statement))

        assume_role_policy = iamrole_item.config.get("assume_role_policy_document", {})
        statement = assume_role_policy.get("Statement", [])
        if type(statement) is list:
            for single_statement in statement:
                check_statement(single_statement)
        elif type(statement) is dict:
            check_statement(statement)

    def check_star_privileges(self, iamrole_item):
        """
        alert when an IAM Role has a policy allowing '*'.
        """
        self.library_check_iamobj_has_star_privileges(iamrole_item, policies_key='rolepolicies')

    def check_iam_star_privileges(self, iamrole_item):
        """
        alert when an IAM Role has a policy allowing 'iam:*'.
        """
        self.library_check_iamobj_has_iam_star_privileges(iamrole_item, policies_key='rolepolicies')

    def check_iam_privileges(self, iamrole_item):
        """
        alert when an IAM Role has a policy allowing 'iam:XxxxxXxxx'.
        """
        self.library_check_iamobj_has_iam_privileges(iamrole_item, policies_key='rolepolicies')

    def check_iam_passrole(self, iamrole_item):
        """
        alert when an IAM Role has a policy allowing 'iam:PassRole'.
        This allows the role to pass any role specified in the resource block to an ec2 instance.
        """
        self.library_check_iamobj_has_iam_passrole(iamrole_item, policies_key='rolepolicies')

    def check_notaction(self, iamrole_item):
        """
        alert when an IAM Role has a policy containing 'NotAction'.
        NotAction combined with an "Effect": "Allow" often provides more privilege
        than is desired.
        """
        self.library_check_iamobj_has_notaction(iamrole_item, policies_key='rolepolicies')

    def check_security_group_permissions(self, iamrole_item):
        """
        alert when an IAM Role has ec2:AuthorizeSecurityGroupEgress or ec2:AuthorizeSecurityGroupIngress.
        """
        self.library_check_iamobj_has_security_group_permissions(iamrole_item, policies_key='rolepolicies')
