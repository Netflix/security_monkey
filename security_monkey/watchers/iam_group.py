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
.. module: security_monkey.watchers.iam_group
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

from boto.exception import BotoServerError

import json
import urllib
import time


class IAMGroup(Watcher):
  index = 'iamgroup'
  i_am_singular = 'IAM Group'
  i_am_plural = 'IAM Groups'

  def __init__(self, accounts=None, debug=False):
    super(IAMGroup, self).__init__(accounts=accounts, debug=debug)

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
        groups_response = self.wrap_aws_rate_limited_call(iam.get_all_groups)
      except Exception as e:
        exc = BotoConnectionIssue(str(e), 'iamgroup', account, None)
        self.slurp_exception((self.index, account, 'universal'), exc, exception_map)
        continue

      for group in groups_response.groups:
        app.logger.debug("Slurping %s (%s) from %s" % (self.i_am_singular, group.group_name, account))

        ### Check if this Group is on the Ignore List ###
        ignore_item = False
        for ignore_item_name in IGNORE_PREFIX[self.index]:
          if group.group_name.lower().startswith(ignore_item_name.lower()):
            ignore_item = True
            break

        if ignore_item:
          continue

        item_config = {
          'group': {},
          'grouppolicies': {},
          'users': {}
        }

        item_config['group'] = dict(group)

        ### GROUP POLICIES ###
        group_policies = self.wrap_aws_rate_limited_call(iam.get_all_group_policies, group.group_name)
        group_policies = group_policies.policy_names

        for policy_name in group_policies:
          policy = self.wrap_aws_rate_limited_call(iam.get_group_policy, group.group_name, policy_name)
          policy = policy.policy_document
          policy = urllib.unquote(policy)
          try:
            policydict = json.loads(policy)
          except:
            exc = InvalidAWSJSON(policy)
            self.slurp_exception((self.index, account, 'universal', group.group_name), exc, exception_map)

          item_config['grouppolicies'][policy_name] = dict(policydict)

        ### GROUP USERS ###
        group_users = self.wrap_aws_rate_limited_call(iam.get_group, group_name=group['group_name'])
        group_users = group_users.users
        for user in group_users:
          item_config['users'][user.arn] = user.user_name

        item = IAMGroupItem(account=account, name=group.group_name, config=item_config)
        item_list.append(item)

    return item_list, exception_map


class IAMGroupItem(ChangeItem):
  def __init__(self, account=None, name=None, config={}):
    super(IAMGroupItem, self).__init__(
      index=IAMGroup.index,
      region='universal',
      account=account,
      name=name,
      new_config=config)