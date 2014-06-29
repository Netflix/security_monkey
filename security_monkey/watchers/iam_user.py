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
.. module: security_monkey.watchers.iam_user
    :platform: Unix

.. version:: $$VERSION$$
.. moduleauthor:: Patrick Kelley <pkelley@netflix.com> @monkeysecurity

"""

from security_monkey.watcher import Watcher
from security_monkey.watcher import ChangeItem
from security_monkey.exceptions import InvalidAWSJSON
from security_monkey.exceptions import BotoConnectionIssue
from security_monkey.constants import IGNORE_PREFIX
from security_monkey import app

import json
import urllib


class IAMUser(Watcher):
  index = 'iamuser'
  i_am_singular = 'IAM User'
  i_am_plural = 'IAM Users'

  def __init__(self, accounts=None, debug=False):
    super(IAMUser, self).__init__(accounts=accounts, debug=debug)

  def slurp(self):
    """
    :returns: item_list - list of IAM Groups.
    :returns: exception_map - A dict where the keys are a tuple containing the
        location of the exception and the value is the actual exception
    """
    item_list = []
    exception_map = {}

    from security_monkey.common.sts_connect import connect
    for account in self.accounts:

      try:
        iam = connect(account, 'iam')
        users_response = iam.get_all_users()
      except Exception as e:
        exc = BotoConnectionIssue(str(e), 'iamgroup', account, None)
        self.slurp_exception((self.index, account, 'universal'), exc, exception_map)
        continue

      for user in users_response.users:
        
        ### Check if this User is on the Ignore List ###
        ignore_item = False
        for ignore_item_name in IGNORE_PREFIX[self.index]:
          if user.user_name.lower().startswith(ignore_item_name.lower()):
            ignore_item = True
            break

        if ignore_item:
          continue        
        
        item_config = {
          'user': {},
          'userpolicies': {},
          'accesskeys': {},
          'mfadevices': {},
          'signingcerts': {}
        }
        app.logger.debug("Slurping %s (%s) from %s" % (self.i_am_singular, user.user_name, account))
        item_config['user'] = dict(user)

        for policy_name in iam.get_all_user_policies(user.user_name).policy_names:
          policy = urllib.unquote(iam.get_user_policy(user.user_name, policy_name).policy_document)
          try:
            policydict = json.loads(policy)
          except:
            exc = InvalidAWSJSON(policy)
            self.slurp_exception((self.index, account, 'universal', user.user_name), exc, exception_map)

          item_config['userpolicies'][policy_name] = dict(policydict)

        for key in iam.get_all_access_keys(user_name=user.user_name).access_key_metadata:
          item_config['accesskeys'][key.access_key_id] = dict(key)

        for mfa in iam.get_all_mfa_devices(user_name=user.user_name).mfa_devices:
          item_config['mfadevices'][mfa.serial_number] = dict(mfa)

        login_profile = 'undefined'
        try:
          login_profile = iam.get_login_profiles(user.user_name).login_profile
          item_config['loginprofile'] = dict(login_profile)
        except:
          pass

        for cert in iam.get_all_signing_certs(user_name=user.user_name).certificates:
          _cert = dict(cert)
          del _cert['certificate_body']
          item_config['signingcerts'][cert.certificate_id] = dict(_cert)

        item_list.append(
          IAMUserItem(account=account, name=user.user_name, config=item_config)
        )

    return item_list, exception_map


class IAMUserItem(ChangeItem):
  def __init__(self, account=None, name=None, config={}):
    super(IAMUserItem, self).__init__(
      index=IAMUser.index,
      region='universal',
      account=account,
      name=name,
      new_config=config)
