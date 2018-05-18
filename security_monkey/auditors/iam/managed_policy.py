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
from security_monkey import ARN_PREFIX


def is_aws_managed_policy(item):
    return ARN_PREFIX + ':iam::aws:policy/' in item.config['arn']


def has_attached_resources(item):
    if 'attached_users' in item.config and len(item.config['attached_users']) > 0:
        return True
    elif 'attached_roles' in item.config and len(item.config['attached_roles']) > 0:
        return True
    elif 'attached_groups' in item.config and len(item.config['attached_groups']) > 0:
        return True
    else:
        return False


class ManagedPolicyAuditor(IAMPolicyAuditor):
    index = ManagedPolicy.index
    i_am_singular = ManagedPolicy.i_am_singular
    i_am_plural = ManagedPolicy.i_am_plural

    def __init__(self, accounts=None, debug=False):
        super(ManagedPolicyAuditor, self).__init__(accounts=accounts, debug=debug)
        self.iam_policy_keys = ['policy']

    def check_star_privileges(self, item):
        """
        alert when an IAM Object has a policy allowing '*'.
        """
        if not is_aws_managed_policy(item) or (is_aws_managed_policy(item) and has_attached_resources(item)):
            super(ManagedPolicyAuditor, self).check_star_privileges(item)

    def check_iam_star_privileges(self, item):
        """
        alert when an IAM Object has a policy allowing 'iam:*'.
        """
        if not is_aws_managed_policy(item) or (is_aws_managed_policy(item) and has_attached_resources(item)):
            super(ManagedPolicyAuditor, self).check_iam_star_privileges(item)

    def check_permissions(self, item):
        """
        Alert when an IAM Object has a policy allowing permission modification.
        """
        if not is_aws_managed_policy(item) or (is_aws_managed_policy(item) and has_attached_resources(item)):
            super(ManagedPolicyAuditor, self).check_permissions(item)

    def check_mutable_sensitive_services(self, item):
        """
        Alert when an IAM Object has DataPlaneMutating permissions for sensitive services.
        """
        if not is_aws_managed_policy(item) or (is_aws_managed_policy(item) and has_attached_resources(item)):
            super(ManagedPolicyAuditor, self).check_mutable_sensitive_services(item)

    def check_iam_passrole(self, item):
        """
        alert when an IAM Object has a policy allowing 'iam:PassRole'.
        This allows the object to pass any role specified in the resource block to an ec2 instance.
        """
        if not is_aws_managed_policy(item) or (is_aws_managed_policy(item) and has_attached_resources(item)):
            super(ManagedPolicyAuditor, self).check_iam_passrole(item)

    def check_notaction(self, item):
        """
        alert when an IAM Object has a policy containing 'NotAction'.
        NotAction combined with an "Effect": "Allow" often provides more privilege
        than is desired.
        """
        if not is_aws_managed_policy(item) or (is_aws_managed_policy(item) and has_attached_resources(item)):
            super(ManagedPolicyAuditor, self).check_notaction(item)

    def check_notresource(self, item):
        """
        alert when an IAM Object has a policy containing 'NotResource'.
        NotResource combined with an "Effect": "Allow" often provides more privilege
        than is desired.
        """
        if not is_aws_managed_policy(item) or (is_aws_managed_policy(item) and has_attached_resources(item)):
            super(ManagedPolicyAuditor, self).check_notresource(item)

    def check_security_group_permissions(self, item):
        """
        alert when an IAM Object has ec2:AuthorizeSecurityGroupEgress or ec2:AuthorizeSecurityGroupIngress.
        """
        if not is_aws_managed_policy(item) or (is_aws_managed_policy(item) and has_attached_resources(item)):
            super(ManagedPolicyAuditor, self).check_security_group_permissions(item)
