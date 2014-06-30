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
from security_monkey.auditor import Auditor
from security_monkey.watchers.iam_user import IAMUser


class IAMUserAuditor(Auditor):
  index = IAMUser.index
  i_am_singular = IAMUser.i_am_singular
  i_am_plural = IAMUser.i_am_plural

  def __init__(self, accounts=None, debug=False):
    super(IAMUserAuditor, self).__init__(accounts=accounts, debug=debug)

  def check_iamuser_has_access_keys(self, iamuser_item):
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
