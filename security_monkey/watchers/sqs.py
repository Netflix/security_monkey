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
from security_monkey.datastore import Account
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
        self.honor_ephemerals = True
        self.ephemeral_paths = [
            'ApproximateNumberOfMessagesNotVisible',
            'ApproximateNumberOfMessages',
            'ApproximateNumberOfMessagesDelayed']

    def slurp(self):
        """
        :returns: item_list - list of SQS Policies.
        :returns: exception_map - A dict where the keys are a tuple containing the
            location of the exception and the value is the actual exception

        """
        self.prep_for_slurp()

        item_list = []
        exception_map = {}
        from security_monkey.common.sts_connect import connect
        for account in self.accounts:
            account_db = Account.query.filter(Account.name == account).first()
            account_number = account_db.identifier
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
                        self.slurp_exception((self.index, account, region.name), exc, exception_map,
                                             source="{}-watcher".format(self.index))
                    continue
                app.logger.debug("Found {} {}".format(len(all_queues), SQS.i_am_plural))
                for q in all_queues:

                    if self.check_ignore_list(q.name):
                        continue

                    try:
                        attrs = self.wrap_aws_rate_limited_call(
                            q.get_attributes,
                            attributes='All'
                        )
                        try:
                            if 'Policy' in attrs:
                                json_str = attrs['Policy']
                                attrs['Policy'] = json.loads(json_str)
                            else:
                                attrs['Policy'] = {}

                            item = SQSItem(region=region.name, account=account, name=q.name, arn=attrs['QueueArn'],
                                           config=dict(attrs))
                            item_list.append(item)
                        except:
                            self.slurp_exception((self.index, account, region, q.name), InvalidAWSJSON(json_str),
                                                 exception_map, source="{}-watcher".format(self.index))
                    except boto.exception.SQSError:
                        # A number of Queues are so ephemeral that they may be gone by the time
                        # the code reaches here.  Just ignore them and move on.
                        pass
        return item_list, exception_map


class SQSItem(ChangeItem):
    def __init__(self, region=None, account=None, name=None, arn=None, config={}):
        super(SQSItem, self).__init__(
            index=SQS.index,
            region=region,
            account=account,
            name=name,
            arn=arn,
            new_config=config)
