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
.. module: security_monkey.watchers.sns
    :platform: Unix

.. version:: $$VERSION$$
.. moduleauthor:: Patrick Kelley <pkelley@netflix.com> @monkeysecurity

"""

from security_monkey.watcher import Watcher
from security_monkey.watcher import ChangeItem
from security_monkey.constants import TROUBLE_REGIONS
from security_monkey.exceptions import InvalidARN
from security_monkey.exceptions import InvalidAWSJSON
from security_monkey.exceptions import BotoConnectionIssue
from security_monkey.constants import IGNORE_PREFIX
from security_monkey import app

import json
import re
from boto.sns import regions


class SNS(Watcher):
  index = 'sns'
  i_am_singular = 'SNS Topic Policy'
  i_am_plural = 'SNS Topic Policies'

  def __init__(self, accounts=None, debug=False):
    super(SNS, self).__init__(accounts=accounts, debug=debug)

  def slurp(self):
    """
    :returns: item_list - list of SNSItem's.
    :returns: exception_map - A dict where the keys are a tuple containing the
        location of the exception and the value is the actual exception

    """
    item_list = []
    exception_map = {}
    for account in self.accounts:
      for region in regions():
        try:
          (sns, topics) = self.get_all_topics_in_region(account, region)
        except Exception as e:
          if region.name not in TROUBLE_REGIONS:
            exc = BotoConnectionIssue(str(e), 'sns', account, region.name)
            self.slurp_exception((self.index, account, region.name), exc, exception_map)
          continue

        app.logger.debug("Found {} {}".format(len(topics), SNS.i_am_plural))
        for topic in topics:
          arn = topic['TopicArn']

          ### Check if this SNS Topic is on the Ignore List ###
          ignore_item = False
          for ignore_item_name in IGNORE_PREFIX[self.index]:
            if arn.lower().startswith(ignore_item_name.lower()):
              ignore_item = True
              break

          if ignore_item:
            continue

          attrs = self.wrap_aws_rate_limited_call(
            sns.get_topic_attributes,
            arn
          )
          item = self.build_item(arn=arn,
                                 attrs=attrs,
                                 region=region.name,
                                 account=account,
                                 exception_map=exception_map)
          if item:
            item_list.append(item)
    return item_list, exception_map

  def get_all_topics_in_region(self, account, region):
    from security_monkey.common.sts_connect import connect
    sns = connect(account, 'sns', region=region)
    app.logger.debug("Checking {}/{}/{}".format(SNS.index, account, region.name))
    topics = []
    marker = None
    while True:
      topics_response = self.wrap_aws_rate_limited_call(
        sns.get_all_topics,
        next_token=marker
      )
      current_page_topics = topics_response['ListTopicsResponse']['ListTopicsResult']['Topics']
      topics.extend(current_page_topics)
      if topics_response[u'ListTopicsResponse'][u'ListTopicsResult'][u'NextToken']:
        marker = topics_response[u'ListTopicsResponse'][u'ListTopicsResult'][u'NextToken']
      else:
        break
    return (sns, topics)

  def build_item(self, arn=None, attrs=None, region=None, account=None, exception_map={}):
    config = {}
    try:
      json_str = attrs['GetTopicAttributesResponse']['GetTopicAttributesResult']['Attributes']['Policy']
      policy = json.loads(json_str)
      config['SNSPolicy'] = policy
    except:
      self.slurp_exception((self.index, account, region, arn), InvalidAWSJSON(json_str), exception_map)
      return None

    try:
      sns_name = re.search('arn:aws:sns:[a-z0-9-]+:[0-9]+:([a-zA-Z0-9-]+)', arn).group(1)
      config['Name'] = {'Name': sns_name}
    except Exception:
      self.slurp_exception((self.index, account, region, arn), InvalidARN(arn), exception_map)
      return None

    return SNSItem(region=region, account=account, name=arn, config=config)


class SNSItem(ChangeItem):
  def __init__(self, region=None, account=None, name=None, config={}):
    super(SNSItem, self).__init__(
      index=SNS.index,
      region=region,
      account=account,
      name=name,
      new_config=config)