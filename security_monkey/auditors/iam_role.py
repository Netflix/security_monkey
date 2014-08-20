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
.. module: security_monkey.auditors.iam_role
    :platform: Unix

.. version:: $$VERSION$$
.. moduleauthor::  Patrick Kelley <pkelley@netflix.com> @monkeysecurity

"""
from security_monkey.watchers.iam_role import IAMRole
from security_monkey.auditors.iam_policy import IAMPolicyAuditor


class IAMRoleAuditor(IAMPolicyAuditor):
  index = IAMRole.index
  i_am_singular = IAMRole.i_am_singular
  i_am_plural = IAMRole.i_am_plural

  def __init__(self, accounts=None, debug=False):
    super(IAMRoleAuditor, self).__init__(accounts=accounts, debug=debug)

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

  def check_notaction(self, iamrole_item):
      """
      alert when an IAM Role has a policy containing 'NotAction'.
      NotAction combined with an "Effect": "Allow" often provides more privilege
      than is desired.
      """
      self.library_check_iamobj_has_notaction(iamrole_item, policies_key='rolepolicies')

