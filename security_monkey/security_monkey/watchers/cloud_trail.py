#     Copyright 2016 Bridgewater Associates
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
.. module: security_monkey.watchers.cloud_trail
    :platform: Unix

.. version:: $$VERSION$$
.. moduleauthor:: Bridgewater OSS <opensource@bwater.com>



"""
from security_monkey.watcher import Watcher
from security_monkey.watcher import ChangeItem
from security_monkey.constants import TROUBLE_REGIONS
from security_monkey.datastore import store_exception
from security_monkey.exceptions import BotoConnectionIssue
from security_monkey import app
from boto.cloudtrail import regions


class CloudTrail(Watcher):
    index = 'cloudtrail'
    i_am_singular = 'CloudTrail'
    i_am_plural = 'CloudTrails'

    def __init__(self, accounts=None, debug=False):
        super(CloudTrail, self).__init__(accounts=accounts, debug=debug)

    def slurp(self):
        """
        :returns: item_list - list of cloud_trail items.
        :returns: exception_map - A dict where the keys are a tuple containing the
            location of the exception and the value is the actual exception
        """
        self.prep_for_slurp()

        item_list = []
        exception_map = {}
        from security_monkey.common.sts_connect import connect
        for account in self.accounts:
            for region in regions():
                app.logger.debug(
                    "Checking {}/{}/{}".format(self.index, account, region.name))

                try:
                    cloud_trail = connect(
                        account, 'boto3.cloudtrail.client', region=region)
                    app.logger.debug("Cloud Trail is: {}".format(cloud_trail))
                    response = self.wrap_aws_rate_limited_call(
                        cloud_trail.describe_trails
                    )
                    trails = response.get('trailList', [])
                except Exception as e:
                    app.logger.debug("Exception found: {}".format(e))
                    if region.name not in TROUBLE_REGIONS:
                        exc = BotoConnectionIssue(
                            str(e), self.index, account, region.name)
                        self.slurp_exception(
                            (self.index, account, region.name), exc, exception_map)
                    continue
                app.logger.debug("Found {} {}.".format(
                    len(trails), self.i_am_plural))

                for trail in trails:
                    name = trail.get('Name')
                    # Some trails are returned for every region, however, HomeRegion
                    # always refers to the region in which the trail was
                    # created.
                    home_region = trail.get('HomeRegion')
                    trail_enabled = ""
                    try:
                        get_trail_status = self.wrap_aws_rate_limited_call(cloud_trail.get_trail_status,
                                                                           Name=trail['TrailARN'])
                        trail_enabled = get_trail_status["IsLogging"]
                    except Exception as e:
                        app.logger.debug("Issues getting the status of cloudtrail")
                        # Store it to the database:
                        location = (self.index, account, region.name, name)
                        store_exception("cloudtrail", location, e)

                    if self.check_ignore_list(name):
                        continue

                    item_config = {
                        'trail': name,
                        'trail_status': trail_enabled,
                        's3_bucket_name': trail['S3BucketName'],
                        's3_key_prefix': trail.get('S3KeyPrefix'),
                        'sns_topic_name': trail.get('SnsTopicName'),
                        'include_global_service_events': trail.get('IncludeGlobalServiceEvents', False),
                        'is_multi_region_trail': trail.get('IsMultiRegionTrail', False),
                        'home_region': home_region,
                        'trail_arn': trail.get('TrailARN'),
                        'log_file_validation_enabled': trail.get('LogFileValidationEnabled', False),
                        'cloudwatch_logs_log_group_arn': trail.get('CloudWatchLogsLogGroupArn'),
                        'cloudwatch_logs_role_arn': trail.get('CloudWatchLogsRoleArn'),
                        'kms_key_id': trail.get('KmsKeyId'),
                    }

                    # Utilizing home_region here ensures a single, unique entry
                    # for each CloudTrail resource
                    item = CloudTrailItem(
                        region=home_region, account=account, name=name, arn=trail.get('TrailARN'), config=item_config,
                        source_watcher=self)
                    item_list.append(item)

        return item_list, exception_map


class CloudTrailItem(ChangeItem):
    def __init__(self, account=None, region=None, name=None, arn=None, config=None, source_watcher=None):
        super(CloudTrailItem, self).__init__(
            index=CloudTrail.index,
            region=region,
            account=account,
            name=name,
            arn=arn,
            new_config=config if config else {},
            source_watcher=source_watcher)
