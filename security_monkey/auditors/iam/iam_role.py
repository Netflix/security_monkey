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
from security_monkey.watchers.iam.iam_role import IAMRole
from security_monkey.auditors.iam.iam_policy import IAMPolicyAuditor
from security_monkey.auditors.resource_policy_auditor import ResourcePolicyAuditor
from security_monkey.watchers.iam.managed_policy import ManagedPolicy
from security_monkey.datastore import Account

from policyuniverse.arn import ARN
import json


class IAMRoleAuditor(IAMPolicyAuditor, ResourcePolicyAuditor):
    index = IAMRole.index
    i_am_singular = IAMRole.i_am_singular
    i_am_plural = IAMRole.i_am_plural
    support_auditor_indexes = [ManagedPolicy.index]

    def __init__(self, accounts=None, debug=False):
        super(IAMRoleAuditor, self).__init__(accounts=accounts, debug=debug)
        # ResourcePolicyAuditor will look inside AssumeRolePolicyDocument
        # while the IAMPolicyAuditor will inspect the InlinePolicies section.
        self.policy_keys = ["AssumeRolePolicyDocument"]

    def check_star_privileges(self, iamrole_item):
        """
        alert when an IAM Role has a policy allowing '*'.
        """
        self.library_check_iamobj_has_star_privileges(iamrole_item, policies_key='InlinePolicies')

    def check_iam_star_privileges(self, iamrole_item):
        """
        alert when an IAM Role has a policy allowing 'iam:*'.
        """
        self.library_check_iamobj_has_iam_star_privileges(iamrole_item, policies_key='InlinePolicies')

    def check_iam_privileges(self, iamrole_item):
        """
        alert when an IAM Role has a policy allowing 'iam:XxxxxXxxx'.
        """
        self.library_check_iamobj_has_iam_privileges(iamrole_item, policies_key='InlinePolicies')

    def check_iam_passrole(self, iamrole_item):
        """
        alert when an IAM Role has a policy allowing 'iam:PassRole'.
        This allows the role to pass any role specified in the resource block to an ec2 instance.
        """
        self.library_check_iamobj_has_iam_passrole(iamrole_item, policies_key='InlinePolicies')

    def check_notaction(self, iamrole_item):
        """
        alert when an IAM Role has a policy containing 'NotAction'.
        NotAction combined with an "Effect": "Allow" often provides more privilege
        than is desired.
        """
        self.library_check_iamobj_has_notaction(iamrole_item, policies_key='InlinePolicies')

    def check_security_group_permissions(self, iamrole_item):
        """
        alert when an IAM Role has ec2:AuthorizeSecurityGroupEgress or ec2:AuthorizeSecurityGroupIngress.
        """
        self.library_check_iamobj_has_security_group_permissions(iamrole_item, policies_key='InlinePolicies')

    def check_attached_managed_policies(self, iamrole_item):
        """
        alert when an IAM Role is attached to a managed policy with issues
        """
        self.library_check_attached_managed_policies(iamrole_item, 'role')
