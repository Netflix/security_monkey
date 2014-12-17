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
from security_monkey.exceptions import BotoConnectionIssue
from security_monkey.exceptions import S3PermissionsIssue
from security_monkey.exceptions import S3ACLReturnedNoneDisplayName
from security_monkey import app

from boto.s3.connection import OrdinaryCallingFormat
import boto
import json


def get_lifecycle_rules(bhandle):
    lifecycle = []

    try:
        lc = bhandle.get_lifecycle_config()
    except:
        # throws an exception (404) when bucket has no lifecycle configurations
        return lifecycle

    for rule in lc:
        lc_rule = {
            'id': rule.id,
            'status': rule.status,
            'prefix': rule.prefix,
        }

        if rule.transition:
            lc_rule['transition'] = {
                'days': rule.transition.days,
                'date': rule.transition.date,
                'storage_class': rule.transition.storage_class
            }

        if rule.expiration:
            lc_rule['expiration'] = {
                'days': rule.expiration.days,
                'date': rule.expiration.date
            }

        lifecycle.append(lc_rule)

    return lifecycle


class S3(Watcher):
    index = 's3'
    i_am_singular = 'S3 Bucket'
    i_am_plural = 'S3 Buckets'
    region_mappings = dict(APNortheast='ap-northeast-1', APSoutheast='ap-southeast-1', APSoutheast2='ap-southeast-2',
                           DEFAULT='', EU='eu-west-1', SAEast='sa-east-1', USWest='us-west-1', USWest2='us-west-2')

    def __init__(self, accounts=None, debug=False):
        super(S3, self).__init__(accounts=accounts, debug=debug)

    def slurp(self):
        """
        :returns: item_list - list of S3 Buckets.
        :returns: exception_map - A dict where the keys are a tuple containing the
            location of the exception and the value is the actual exception
        """
        self.prep_for_slurp()

        item_list = []
        exception_map = {}

        from security_monkey.common.sts_connect import connect
        for account in self.accounts:

            try:
                s3conn = connect(account, 's3', calling_format=OrdinaryCallingFormat())
                all_buckets = self.wrap_aws_rate_limited_call(
                    s3conn.get_all_buckets
                )
            except Exception as e:
                exc = BotoConnectionIssue(str(e), 's3', account, None)
                self.slurp_exception((self.index, account), exc, exception_map)
                continue

            for bucket in all_buckets:
                app.logger.debug("Slurping %s (%s) from %s" % (self.i_am_singular, bucket.name, account))

                if self.check_ignore_list(bucket.name):
                    continue

                try:
                    loc = self.wrap_aws_rate_limited_call(bucket.get_location)
                    region = self.translate_location_to_region(loc)
                    if region == '':
                        s3regionconn = self.wrap_aws_rate_limited_call(
                            connect,
                            account,
                            's3',
                            calling_format=OrdinaryCallingFormat()
                        )
                        region = 'us-east-1'
                    else:
                        s3regionconn = self.wrap_aws_rate_limited_call(
                            connect,
                            account,
                            's3',
                            region=region,
                            calling_format=OrdinaryCallingFormat()
                        )

                    bhandle = self.wrap_aws_rate_limited_call(
                        s3regionconn.get_bucket,
                        bucket,
                        validate=False
                    )
                    s3regionconn.close()
                except Exception as e:
                    exc = S3PermissionsIssue(bucket.name)
                    # Unfortunately, we can't get the region, so the entire account
                    # will be skipped in find_changes, not just the bad bucket.
                    self.slurp_exception((self.index, account), exc, exception_map)
                    continue

                app.logger.debug("Slurping %s (%s) from %s/%s" % (self.i_am_singular, bucket.name, account, region))
                bucket_dict = self.conv_bucket_to_dict(bhandle, account, region, bucket.name, exception_map)

                item = S3Item(account=account, region=region, name=bucket.name, config=bucket_dict)
                item_list.append(item)

        return item_list, exception_map

    def translate_location_to_region(self, location):
        if location in self.region_mappings:
            return self.region_mappings[location]
        else:
            return location


    def conv_bucket_to_dict(self, bhandle, account, region, bucket_name, exception_map):
        """
        Converts the bucket ACL and Policy information into a python dict that we can save.
        """
        bucket_dict = {}
        grantees = {}
        acl = self.wrap_aws_rate_limited_call(
            bhandle.get_acl
        )
        aclxml = self.wrap_aws_rate_limited_call(
            acl.to_xml
        )
        if '<DisplayName>None</DisplayName>' in aclxml:
            # Boto sometimes returns XML with strings like:
            #   <DisplayName>None</DisplayName>
            # Wait a little while, and it will return the real DisplayName
            # The console will display "Me" as the Grantee when we see these None
            # DisplayNames in boto.
            exc = S3ACLReturnedNoneDisplayName(bucket_name)
            self.slurp_exception((self.index, account, region, bucket_name), exc, exception_map)
        else:
            for grant in acl.acl.grants:

                if grant.display_name == 'None' or grant.display_name == 'null':
                    app.logger.info("Received a bad display name: %s" % grant.display_name)

                if grant.display_name is None:
                    gname = grant.uri
                else:
                    gname = grant.display_name

                if gname in grantees:
                    grantees[gname].append(grant.permission)
                    grantees[gname] = sorted(grantees[gname])
                else:
                    grantees[gname] = [grant.permission]

        bucket_dict['grants'] = grantees

        try:
            policy = self.wrap_aws_rate_limited_call(
                bhandle.get_policy
            )
            policy = json.loads(policy)
            bucket_dict['policy'] = policy
        except boto.exception.S3ResponseError as e:
            # S3ResponseError is raised if there is no policy.
            # Simply ignore.
            pass

        # {} or {'Versioning': 'Enabled'} or {'MfaDelete': 'Disabled', 'Versioning': 'Enabled'}
        bucket_dict['versioning'] = self.wrap_aws_rate_limited_call(
            bhandle.get_versioning_status
        )

        bucket_dict['lifecycle_rules'] = get_lifecycle_rules(bhandle)

        return bucket_dict


class S3Item(ChangeItem):
    def __init__(self, account=None, region=None, name=None, config={}):
        super(S3Item, self).__init__(
            index=S3.index,
            region=region,
            account=account,
            name=name,
            new_config=config)
