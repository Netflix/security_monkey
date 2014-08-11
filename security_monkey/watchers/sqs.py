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
.. module: security_monkey.watchers.sqs
    :platform: Unix

.. version:: $$VERSION$$
.. moduleauthor:: Patrick Kelley <pkelley@netflix.com> @monkeysecurity

"""

from security_monkey.watcher import Watcher
from security_monkey.watcher import ChangeItem
from security_monkey.constants import TROUBLE_REGIONS
from security_monkey.exceptions import InvalidAWSJSON
from security_monkey.exceptions import BotoConnectionIssue
from security_monkey.constants import IGNORE_PREFIX
from security_monkey import app

import json
import boto
from boto.sqs import regions


class SQS(Watcher):
  index = 'sqs'
  i_am_singular = 'SQS Policy'
  i_am_plural = 'SQS Policies'

  def __init__(self, accounts=None, debug=False):
    super(SQS, self).__init__(accounts=accounts, debug=debug)

  def slurp(self):
    """
    :returns: item_list - list of SQS Policies.
    :returns: exception_map - A dict where the keys are a tuple containing the
        location of the exception and the value is the actual exception

    """
    item_list = []
    exception_map = {}
    from security_monkey.common.sts_connect import connect
    for account in self.accounts:
      for region in regions():
        app.logger.debug("Checking {}/{}/{}".format(SQS.index, account, region.name))
        try:
          sqs = connect(account, 'sqs', region=region)
          all_queues = self.wrap_aws_rate_limited_call(
            sqs.get_all_queues
          )
        except Exception as e:
          if region.name not in TROUBLE_REGIONS:
            exc = BotoConnectionIssue(str(e), 'sqs', account, region.name)
            self.slurp_exception((self.index, account, region.name), exc, exception_map)
          continue
        app.logger.debug("Found {} {}".format(len(all_queues), SQS.i_am_plural))
        for q in all_queues:

          ### Check if this Queue is on the Ignore List ###
          ignore_item = False
          for ignore_item_name in IGNORE_PREFIX[self.index]:
            if q.name.lower().startswith(ignore_item_name.lower()):
              ignore_item = True
              break

          if ignore_item:
            continue

          try:
            policy = self.wrap_aws_rate_limited_call(
              q.get_attributes,
              attributes='Policy'
            )
            if 'Policy' in policy:
              try:
                json_str = policy['Policy']
                policy = json.loads(json_str)
                item = SQSItem(region=region.name, account=account, name=q.name,
                               config=policy)
                item_list.append(item)
              except:
                self.slurp_exception((self.index, account, region, q.name), InvalidAWSJSON(json_str), exception_map)
          except boto.exception.SQSError:
            # A number of Queues are so ephemeral that they may be gone by the time
            # the code reaches here.  Just ignore them and move on.
            pass
    return item_list, exception_map


class SQSItem(ChangeItem):
  def __init__(self, region=None, account=None, name=None, config={}):
    super(SQSItem, self).__init__(
      index=SQS.index,
      region=region,
      account=account,
      name=name,
      new_config=config)