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
.. module: security_monkey.auditors.iam_user
    :platform: Unix

.. version:: $$VERSION$$
.. moduleauthor::  Patrick Kelley <pkelley@netflix.com> @monkeysecurity

"""
from security_monkey.watchers.iam_user import IAMUser
from security_monkey.auditors.iam_policy import IAMPolicyAuditor


class IAMUserAuditor(IAMPolicyAuditor):
    index = IAMUser.index
    i_am_singular = IAMUser.i_am_singular
    i_am_plural = IAMUser.i_am_plural

    def __init__(self, accounts=None, debug=False):
        super(IAMUserAuditor, self).__init__(accounts=accounts, debug=debug)

    def check_access_keys(self, iamuser_item):
        """
        alert when an IAM User has an active access key.
        """
        akeys = iamuser_item.config.get('accesskeys', {})
        for akey in akeys.keys():
            if u'status' in akeys[akey]:
                if akeys[akey][u'status'] == u'Active':
                    self.add_issue(1, 'User has active accesskey.', iamuser_item, notes=akey)
                else:
                    self.add_issue(0, 'User has an inactive accesskey.', iamuser_item, notes=akey)

    def check_star_privileges(self, iamuser_item):
        """
        alert when an IAM User has a policy allowing '*'.
        """
        self.library_check_iamobj_has_star_privileges(iamuser_item, policies_key='userpolicies')

    def check_iam_star_privileges(self, iamuser_item):
        """
        alert when an IAM User has a policy allowing 'iam:*'.
        """
        self.library_check_iamobj_has_iam_star_privileges(iamuser_item, policies_key='userpolicies')

    def check_iam_privileges(self, iamuser_item):
        """
        alert when an IAM User has a policy allowing 'iam:XxxxxXxxx'.
        """
        self.library_check_iamobj_has_iam_privileges(iamuser_item, policies_key='userpolicies')

    def check_iam_passrole(self, iamuser_item):
        """
        alert when an IAM User has a policy allowing 'iam:PassRole'.
        This allows the user to pass any role specified in the resource block to an ec2 instance.
        """
        self.library_check_iamobj_has_iam_passrole(iamuser_item, policies_key='userpolicies')

    def check_notaction(self, iamuser_item):
        """
        alert when an IAM User has a policy containing 'NotAction'.
        NotAction combined with an "Effect": "Allow" often provides more privilege
        than is desired.
        """
        self.library_check_iamobj_has_notaction(iamuser_item, policies_key='userpolicies')
