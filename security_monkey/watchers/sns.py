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
        self.prep_for_slurp()

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

                    if self.check_ignore_list(arn):
                        continue

                    item = self.build_item(arn=arn,
                                           conn=sns,
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
        return sns, topics

    def _get_topic_subscriptions(self, sns, arn):
        # paginate over each topic subscription
        token = None
        all_subscriptions = []
        while True:
            subscriptions = self.wrap_aws_rate_limited_call(
                sns.get_all_subscriptions_by_topic,
                arn,
                next_token=token
            )
            all_subscriptions.extend(
                subscriptions['ListSubscriptionsByTopicResponse']['ListSubscriptionsByTopicResult']['Subscriptions']
            )
            token = subscriptions['ListSubscriptionsByTopicResponse']['ListSubscriptionsByTopicResult']['NextToken']
            if token is None:
                break
        return all_subscriptions

    def _get_sns_policy(self, attrs, account, region, arn, exception_map):
        try:
            json_str = attrs['GetTopicAttributesResponse']['GetTopicAttributesResult']['Attributes']['Policy']
            return json.loads(json_str)
        except:
            self.slurp_exception((self.index, account, region, arn), InvalidAWSJSON(json_str), exception_map)
            raise

    def _get_sns_name(self, arn, account, region, exception_map):
        try:
            return re.search('arn:aws:sns:[a-z0-9-]+:[0-9]+:([a-zA-Z0-9-]+)', arn).group(1)
        except:
            self.slurp_exception((self.index, account, region, arn), InvalidARN(arn), exception_map)
            raise

    def build_item(self, arn=None, conn=None, region=None, account=None, exception_map={}):
        config = {}

        try:
            attrs = self.wrap_aws_rate_limited_call(
                conn.get_topic_attributes,
                arn
            )

            config['subscriptions'] = self._get_topic_subscriptions(conn, arn)
            config['policy'] = self._get_sns_policy(attrs, account, region, arn, exception_map)
            config['name'] = self._get_sns_name(arn, account, region, exception_map)
        except:
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
