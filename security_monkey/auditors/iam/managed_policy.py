#     Copyright 2015 Netflix, Inc.
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
.. module: security_monkey.auditors.iam.managed_policy
    :platform: Unix

.. version:: $$VERSION$$
.. moduleauthor::  Patrick Kelley <pkelley@netflix.com> @monkeysecurity

"""
from security_monkey.watchers.iam.managed_policy import ManagedPolicy
from security_monkey.auditors.iam.iam_policy import IAMPolicyAuditor


class ManagedPolicyAuditor(IAMPolicyAuditor):
    index = ManagedPolicy.index
    i_am_singular = ManagedPolicy.i_am_singular
    i_am_plural = ManagedPolicy.i_am_plural

    def __init__(self, accounts=None, debug=False):
        super(ManagedPolicyAuditor, self).__init__(accounts=accounts, debug=debug)

    def prep_for_audit(self):
        """
        No prep necessary.
        """
        pass

    def check_star_privileges(self, iam_object):
        """
        alert when an IAM Object has a policy allowing '*'.
        """
        self.library_check_iamobj_has_star_privileges(
            iam_object,
            policies_key='policy',
            multiple_policies=False
        )

    def check_iam_star_privileges(self, iam_object):
        """
        alert when an IAM Object has a policy allowing 'iam:*'.
        """
        self.library_check_iamobj_has_iam_star_privileges(
            iam_object,
            policies_key='policy',
            multiple_policies=False
        )

    def check_iam_privileges(self, iam_object):
        """
        alert when an IAM Object has a policy allowing 'iam:XxxxxXxxx'.
        """
        self.library_check_iamobj_has_iam_privileges(
            iam_object,
            policies_key='policy',
            multiple_policies=False
        )

    def check_iam_passrole(self, iam_object):
        """
        alert when an IAM Object has a policy allowing 'iam:PassRole'.
        This allows the object to pass any role specified in the resource block to an ec2 instance.
        """
        self.library_check_iamobj_has_iam_passrole(
            iam_object,
            policies_key='policy',
            multiple_policies=False
        )

    def check_notaction(self, iam_object):
        """
        alert when an IAM Object has a policy containing 'NotAction'.
        NotAction combined with an "Effect": "Allow" often provides more privilege
        than is desired.
        """
        self.library_check_iamobj_has_notaction(
            iam_object,
            policies_key='policy',
            multiple_policies=False
        )

    def check_security_group_permissions(self, iam_object):
        """
        alert when an IAM Object has ec2:AuthorizeSecurityGroupEgress or ec2:AuthorizeSecurityGroupIngress.
        """
        self.library_check_iamobj_has_security_group_permissions(
            iam_object,
            policies_key='policy',
            multiple_policies=False
        )

