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
from cloudaux.aws.sqs import list_queues
from cloudaux.orchestration.aws.sqs import get_queue

from security_monkey.cloudaux_batched_watcher import CloudAuxBatchedWatcher


class SQS(CloudAuxBatchedWatcher):
    index = 'sqs'
    i_am_singular = 'SQS Policy'
    i_am_plural = 'SQS Policies'

    def __init__(self, **kwargs):
        super(SQS, self).__init__(**kwargs)
        self.honor_ephemerals = True
        self.ephemeral_paths = [
            '_version',
            'Attributes$*$LastModifiedTimestamp',
            'Attributes$*$ApproximateNumberOfMessagesNotVisible',
            'Attributes$*$ApproximateNumberOfMessages',
            'Attributes$*$ApproximateNumberOfMessagesDelayed'
        ]
        self.batched_size = 200

    def get_name_from_list_output(self, item):
        # SQS returns URLs. Need to deconstruct the URL to pull out the name :/
        name = item.split("{}/".format(self.account_identifiers[0]))[1]

        return name

    def list_method(self, **kwargs):
        return list_queues(**kwargs)

    def get_method(self, item, **kwargs):
        return get_queue(item, **kwargs)
