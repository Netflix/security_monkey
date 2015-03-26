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
import datetime

from dateutil import parser
from dateutil import tz

from security_monkey.watchers.iam.iam_user import IAMUser
from security_monkey.auditors.iam_policy import IAMPolicyAuditor


class IAMUserAuditor(IAMPolicyAuditor):
    index = IAMUser.index
    i_am_singular = IAMUser.i_am_singular
    i_am_plural = IAMUser.i_am_plural

    def __init__(self, accounts=None, debug=False):
        super(IAMUserAuditor, self).__init__(accounts=accounts, debug=debug)

    def prep_for_audit(self):
        """
        Prepare for the audit by calculating 90 days ago.
        This is used to check if access keys have been rotated.
        """
        now = datetime.datetime.now()
        then = now - datetime.timedelta(days=90)
        self.ninety_days_ago = then.replace(tzinfo=tz.gettz('UTC'))

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

    def check_access_key_rotation(self, iamuser_item):
        """
        alert when an IAM User has an active access key created more than 90 days go.
        """
        akeys = iamuser_item.config.get('accesskeys', {})
        for akey in akeys.keys():
            if u'status' in akeys[akey]:
                if akeys[akey][u'status'] == u'Active':
                    create_date = akeys[akey][u'create_date']
                    create_date = parser.parse(create_date)
                    if create_date < self.ninety_days_ago:
                        notes = "> 90 days ago"
                        self.add_issue(1, 'Active accesskey has not been rotated.', iamuser_item, notes=notes)

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

    def check_security_group_permissions(self, iamuser_item):
        """
        alert when an IAM User has ec2:AuthorizeSecurityGroupEgress or ec2:AuthorizeSecurityGroupIngress.
        """
        self.library_check_iamobj_has_security_group_permissions(iamuser_item, policies_key='userpolicies')

    def check_no_mfa(self, iamuser_item):
        """
        alert when an IAM user has a login profile and no MFA devices.
        This means a human account which could be better protected with 2FA.
        """
        mfas = iamuser_item.config.get('mfadevices', {})
        loginprof = iamuser_item.config.get('loginprofile', {})
        has_active_mfas = False
        has_login_profile = False
        if mfas:
            has_active_mfas = True
        if loginprof != {}:
            has_login_profile = True
        if has_login_profile and not has_active_mfas:
            self.add_issue(1, 'User with password login and no MFA devices.', iamuser_item)

    def check_loginprofile_plus_akeys(self, iamuser_item):
        """
        alert when an IAM user has a login profile and API access via access keys.
        An account should be used Either for API access OR for console access, but maybe not both.
        """
        if not iamuser_item.config.get('loginprofile', None):
            return

        akeys = iamuser_item.config.get('accesskeys', {})
        for akey in akeys.keys():
            if u'status' in akeys[akey] and akeys[akey][u'status'] == u'Active':
                self.add_issue(1, 'User with password login and API access.', iamuser_item)
                return
