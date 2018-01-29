#     Copyright 2018 Netflix, Inc.
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
.. moduleauthor:: Mike Grima <mgrima@netflix.com>
"""
from botocore.exceptions import ClientError
from cloudaux.aws.sqs import list_queues
from cloudaux.orchestration.aws.sqs import get_queue

from security_monkey import app
from security_monkey.cloudaux_batched_watcher import CloudAuxBatchedWatcher


class SQS(CloudAuxBatchedWatcher):
    index = 'sqs'
    i_am_singular = 'SQS Policy'
    i_am_plural = 'SQS Policies'

    def __init__(self, **kwargs):
        super(SQS, self).__init__(**kwargs)
        self.service_name = "sqs"
        self.honor_ephemerals = True
        self.ephemeral_paths = [
            '_version',
            'Attributes$LastModifiedTimestamp',
            'Attributes$ApproximateNumberOfMessagesNotVisible',
            'Attributes$ApproximateNumberOfMessages',
            'Attributes$ApproximateNumberOfMessagesDelayed'
        ]
        self.batched_size = 200

        # SQS returns a list of URLs. The DB wants the total list of items to be a dict that contains
        # an "Arn" field. Since that is not present, this is used to help update the list with the ARNs
        # when they are discovered.
        self.corresponding_items = {}

    def get_name_from_list_output(self, item):
        # SQS returns URLs. Need to deconstruct the URL to pull out the name :/
        app.logger.debug("[ ] Processing SQS Queue with URL: {}".format(item["Url"]))

        name = item["Url"].split("{}/".format(self.account_identifiers[0]))[1]

        return name

    def list_method(self, **kwargs):
        """
        Get the list of SQS queues. Also, create the corresponding lookup table with URL -> position
        in the total list.
        :param kwargs:
        :return:
        """
        items = []
        queues = list_queues(**kwargs)

        # Offset by the existing items in the list (from other regions)
        offset = len(self.corresponding_items)
        queue_count = -1

        for item_count in range(0, len(queues)):
            if self.corresponding_items.get(queues[item_count]):
                app.logger.error("[?] Received a duplicate item in the SQS list: {}. Skipping it.".format(queues[item_count]))
                continue
            queue_count += 1
            items.append({"Url": queues[item_count], "Region": kwargs["region"]})
            self.corresponding_items[queues[item_count]] = queue_count + offset

        return items

    def get_method(self, item, **kwargs):
        try:
            queue = get_queue(item["Url"], **kwargs)

            # Update the current position in the total list by replacing the SQS queue URL with
            # the ARN of the queue
            self.total_list[self.corresponding_items[item["Url"]]] = {"Arn": queue["Arn"]}
        except ClientError as ce:
            # In case the queue was created and then deleted really quickly:
            if "NonExistentQueue" in ce.response["Error"]["Code"]:
                app.logger.debug("Queue with URL: {} - was listed, but is no longer present".format(item["Url"]))
                return
            else:
                raise ce

        return queue
