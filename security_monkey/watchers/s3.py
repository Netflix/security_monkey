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

from security_monkey.watcher import Watcher
from security_monkey.watcher import ChangeItem
from security_monkey.decorators import record_exception
from security_monkey.decorators import iter_account_region
from security_monkey import app

from botocore.exceptions import ClientError
import json


class S3(Watcher):
    index = 's3'
    i_am_singular = 'S3 Bucket'
    i_am_plural = 'S3 Buckets'
    region_mappings = dict(APNortheast='ap-northeast-1', APSoutheast='ap-southeast-1', APSoutheast2='ap-southeast-2',
                           DEFAULT='', EU='eu-west-1', SAEast='sa-east-1', USWest='us-west-1', USWest2='us-west-2')

    @record_exception(source="s3-watcher")
    def all_buckets(self, **kwargs):
        from security_monkey.common.sts_connect import connect
        s3_resource = connect(kwargs['account_name'], 'boto3.s3.resource')
        buckets = s3_resource.buckets.all()
        return [bucket for bucket in buckets if not self.check_ignore_list(bucket.name)]

    @record_exception(source="s3-watcher")
    def get_region_connection(self, bucket, **kwargs):
        """
        Gets the region constraints of the bucket and creates a region specific
        connection if necessary
        """
        from security_monkey.common.sts_connect import connect
        s3 = connect(kwargs['account_name'], 'boto3.s3.client',
                     region='us-east-1', assumed_role=kwargs['assumed_role'])

        # Some s3 buckets do not allow viewing of details. We do not want to
        # throw an error in this case because we still want to see that the
        # bucket exists
        try:
            result = self.wrap_aws_rate_limited_call(s3.get_bucket_location, Bucket=bucket)
        except ClientError, e:
            if 'AccessDenied' not in str(e):
                raise e
            return None

        location = result['LocationConstraint']

        if location is None:
            region = 'us-east-1'
        else:
            if location in self.region_mappings:
                region = self.region_mappings[location]
            else:
                region = location
            s3 = connect(kwargs['account_name'], 'boto3.s3.client',
                         region=region, assumed_role=kwargs['assumed_role'])

        return s3

    @record_exception(source="s3-watcher")
    def get_bucket_acl(self, s3, bucket, **kwargs):
        """
        Returns bucket access control info
        """
        acl = self.wrap_aws_rate_limited_call(
            s3.get_bucket_acl, Bucket=bucket
        )

        grantees = {}

        for grant in acl['Grants']:
            grantee = grant['Grantee']

            display_name = grantee.get('DisplayName')
            if display_name == 'None' or display_name == 'null':
                app.logger.info("Received a bad display name: %s", display_name)

            if display_name is None:
                gname = grantee.get('URI')
            else:
                gname = grantee['DisplayName']

            if gname in grantees:
                grantees[gname].append(grant['Permission'])
                grantees[gname] = sorted(grantees[gname])
            else:
                grantees[gname] = [grant['Permission']]

        return grantees

    @record_exception(source="s3-watcher")
    def get_bucket_policy(self, s3, bucket, **kwargs):
        try:
            result = self.wrap_aws_rate_limited_call(
                s3.get_bucket_policy, Bucket=bucket
            )
            return json.loads(result['Policy'])
        except ClientError as e:
            if 'NoSuchBucketPolicy' not in str(e):
                raise e
            return None

    @record_exception(source="s3-watcher")
    def get_bucket_tagging(self, s3, bucket, **kwargs):
        try:
            result = self.wrap_aws_rate_limited_call(
                s3.get_bucket_tagging, Bucket=bucket
            )
            tags = result['TagSet']
            tag_dict = {}
            for tagset in tags:
                tag_dict[tagset['Key']] = tagset['Value']

            return tag_dict
        except ClientError as e:
            if 'NoSuchTagSet' not in str(e):
                raise e
            return None

    @record_exception(source="s3-watcher")
    def get_bucket_versioning(self, s3, bucket, **kwargs):
        # # {} or {'Versioning': 'Enabled'} or {'MfaDelete': 'Disabled', 'Versioning': 'Enabled'}
        result = self.wrap_aws_rate_limited_call(
            s3.get_bucket_versioning, Bucket=bucket
        )
        versioning = {}
        if result.get('Status'):
            versioning['Versioning'] = result['Status']
        if result.get('MFADelete'):
            versioning['MFADelete'] = result['MFADelete']

        return versioning

    @record_exception(source="s3-watcher")
    def get_bucket_lifecycle_configuration(self, s3, bucket, **kwargs):
        lifecycle_dict = []

        try:
            result = self.wrap_aws_rate_limited_call(
                s3.get_bucket_lifecycle_configuration, Bucket=bucket
            )

            rules = result['Rules']
            for rule in rules:
                rule_dict = {
                    'id': rule['ID'],
                    'status': rule['Status'],
                    'prefix': rule['Prefix'],
                }

                if rule.get('Transitions'):
                    transition_list = []
                    for transition in rule['Transitions']:
                        transition_dict = {}
                        if transition.get('Days'):
                            transition_dict['days'] = transition['Days']
                        if transition.get('Date'):
                            transition_dict['date'] = transition['Date'].strftime('%Y-%m-%dT%H:%M:%SZ')
                        transition_dict['storage_class'] = transition['StorageClass']
                        transition_list.append(transition_dict)

                    rule_dict['transitions'] = transition_list

                if rule.get('Expiration'):
                    expiration_dict = {}
                    expiration = rule['Expiration']
                    if expiration.get('Days'):
                        expiration_dict['days'] = expiration['Days']
                    if expiration.get('Date'):
                        expiration_dict['date'] = expiration['Date'].strftime('%Y-%m-%dT%H:%M:%SZ')

                    rule_dict['expiration'] = expiration_dict

                lifecycle_dict.append(rule_dict)
        except ClientError as e:
            if 'NoSuchLifecycleConfiguration' not in str(e):
                raise e

        return lifecycle_dict

    @record_exception(source="s3-watcher")
    def get_bucket_logging(self, s3, bucket, **kwargs):
        logging_dict = {}
        result = self.wrap_aws_rate_limited_call(
            s3.get_bucket_logging, Bucket=bucket
        )

        if result.get('LoggingEnabled'):
            logging = result['LoggingEnabled']
            logging_dict['enabled'] = True
            logging_dict['prefix'] = logging['TargetPrefix']
            logging_dict['target'] = logging['TargetBucket']
            grant_list = []
            if logging.get('TargetGrants'):
                for grant in logging['TargetGrants']:
                    grant_dict = {}
                    grant_dict['permission'] = grant['Permission']
                    grantee = grant['Grantee']
                    grant_dict['type'] = grantee['Type']
                    if grantee['Type'] == 'CanonicalUser':
                        grant_dict['display_name'] = grantee['DisplayName']
                    elif grantee['Type'] == 'Group':
                        grant_dict['group_uri'] = grantee['URI']
                    else:
                        grant_dict['email'] = grantee['EmailAddress']
                grant_list.append(grant_dict)

            logging_dict['grants'] = grant_list

        return logging_dict

    def slurp(self):
        """
        :returns: item_list - list of S3 Buckets.
        :returns: exception_map - A dict where the keys are a tuple containing the
            location of the exception and the value is the actual exception
        """
        self.prep_for_slurp()

        @iter_account_region(index=self.index, accounts=self.accounts)
        def slurp_items(**kwargs):
            item_list = []
            account = kwargs['account_name']

            all_buckets = self.all_buckets(**kwargs)

            for bucket in all_buckets:
                s3 = None
                app.logger.info("Slurping %s (%s) from %s" % (self.i_am_singular, bucket.name, account))

                s3 = self.get_region_connection(bucket.name, **kwargs)

                bucket_dict = {
                    'arn': "arn:aws:s3:::{name}".format(name=bucket.name)
                }

                if s3 is None:
                    region = 'us-east-1'
                    bucket_dict['Error'] = "Unauthorized"
                else:
                    region = s3.__dict__['_client_config'].region_name
                    bucket_dict['grants'] = self.get_bucket_acl(s3, bucket.name, **kwargs)
                    policy = self.get_bucket_policy(s3, bucket.name, **kwargs)
                    if policy:
                        bucket_dict['policy'] = policy

                    tags = self.get_bucket_tagging(s3, bucket.name, **kwargs)
                    if tags:
                        bucket_dict['tags'] = tags

                    bucket_dict['versioning'] = self.get_bucket_versioning(s3, bucket.name, **kwargs)
                    bucket_dict['lifecycle_rules'] = self.get_bucket_lifecycle_configuration(s3, bucket.name, **kwargs)
                    bucket_dict['logging'] = self.get_bucket_logging(s3, bucket.name, **kwargs)

                item = S3Item(account=account, region=region, name=bucket.name,
                              config=bucket_dict)

                item_list.append(item)

            return item_list, kwargs['exception_map']
        return slurp_items()


class S3Item(ChangeItem):
    def __init__(self, account=None, region=None, name=None, config={}):
        super(S3Item, self).__init__(
            index=S3.index,
            region=region,
            account=account,
            name=name,
            arn="arn:aws:s3:::{name}".format(name=name),
            new_config=config)
