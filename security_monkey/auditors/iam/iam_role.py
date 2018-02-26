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
        self.iam_policy_keys = ['InlinePolicies$*']

    def check_attached_managed_policies(self, iamrole_item):
        """
        alert when an IAM Role is attached to a managed policy with issues
        """
        self.library_check_attached_managed_policies(iamrole_item, 'role')
