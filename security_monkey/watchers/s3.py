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
.. module: security_monkey.watchers.s3
    :platform: Unix

.. version:: $$VERSION$$
.. moduleauthor:: Patrick Kelley <pkelley@netflix.com> @monkeysecurity

"""
from cloudaux.orchestration.aws.s3 import get_bucket
from cloudaux.aws.s3 import list_buckets
from security_monkey.decorators import record_exception, iter_account_region
from security_monkey.watcher import ChangeItem
from security_monkey.watcher import Watcher
from security_monkey import app


class S3(Watcher):
    index = 's3'
    i_am_singular = 'S3 Bucket'
    i_am_plural = 'S3 Buckets'

    def __init__(self, accounts=None, debug=False):
        super(S3, self).__init__(accounts=accounts, debug=debug)

    @record_exception(source="s3-watcher", pop_exception_fields=True)
    def list_buckets(self, **kwargs):
        buckets = list_buckets(**kwargs)
        return [bucket['Name'] for bucket in buckets['Buckets'] if not self.check_ignore_list(bucket['Name'])]

    @record_exception(source="s3-watcher", pop_exception_fields=True)
    def process_bucket(self, bucket, **kwargs):
        app.logger.debug("Slurping {index} ({name}) from {account}".format(
            index=self.i_am_singular,
            name=bucket,
            account=kwargs['account_number']))
        return get_bucket(bucket, **kwargs)

    def slurp(self):
        self.prep_for_slurp()

        @iter_account_region(index=self.index, accounts=self.accounts)
        def slurp_items(**kwargs):
            item_list = []
            bucket_names = self.list_buckets(**kwargs)

            for bucket_name in bucket_names:
                bucket = self.process_bucket(bucket_name, name=bucket_name, **kwargs)
                if bucket:
                    item = S3Item.from_slurp(bucket_name, bucket, **kwargs)
                    item_list.append(item)

            return item_list, kwargs.get('exception_map', {})
        return slurp_items()


class S3Item(ChangeItem):
    def __init__(self, account=None, region='us-east-1', name=None, arn=None, config={}):
        super(S3Item, self).__init__(
            index=S3.index,
            region=region,
            account=account,
            name=name,
            arn=arn,
            new_config=config)

    @classmethod
    def from_slurp(cls, bucket_name, bucket, **kwargs):
        return cls(
            account=kwargs['account_name'],
            name=bucket_name,
            region=bucket['Region'],
            config=bucket,
            arn=bucket['Arn'])
