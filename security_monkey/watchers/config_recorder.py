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
.. module: security_monkey.watchers.config_recorder
    :platform: Unix

.. version:: $$VERSION$$
.. moduleauthor:: Bridgewater OSS <opensource@bwater.com>


"""
from security_monkey.watcher import Watcher
from security_monkey.watcher import ChangeItem
from security_monkey.constants import TROUBLE_REGIONS
from security_monkey.exceptions import BotoConnectionIssue
from security_monkey import app
from boto.ec2 import regions


class ConfigRecorder(Watcher):
    index = 'configrecorder'
    i_am_singular = 'Config Recorder'
    i_am_plural = 'Config Recorders'
    # TODO: Replace hardcoded region with `get_available_regions` after next boto3 release
    # Specific PR here: https://github.com/boto/boto3/pull/531/files
    # AWS Config currently only supports the following regions
    regions = ["us-east-1", "us-west-1", "us-west-2", "eu-west-1", "eu-central-1",
               "ap-northeast-1", "ap-southeast-1", "ap-southeast-2", "sa-east-1"]

    def __init__(self, accounts=None, debug=False):
        super(ConfigRecorder, self).__init__(accounts=accounts, debug=debug)

    def slurp(self):
        """
        :returns: item_list - list of AWS Config recorders.
        :returns: exception_map - A dict where the keys are a tuple containing the
            location of the exception and the value is the actual exception
        """
        self.prep_for_slurp()

        item_list = []
        exception_map = {}
        from security_monkey.common.sts_connect import connect
        for account in self.accounts:
            for region in regions():
                # TODO: Replace hardcoded region with `get_available_regions` after next boto3 release
                # Specific PR here:
                # https://github.com/boto/boto3/pull/531/files
                if region.name in self.regions:
                    app.logger.debug(
                        "Checking {}/{}/{}".format(self.index, account, region.name))

                    try:
                        config_service = connect(
                            account, 'boto3.config.client', region=region)

                        response = self.wrap_aws_rate_limited_call(
                            config_service.describe_configuration_recorders
                        )

                        config_recorders = response.get(
                            'ConfigurationRecorders', [])
                    except Exception as e:
                        app.logger.debug("Exception found: {}".format(e))
                        if region.name not in TROUBLE_REGIONS:
                            exc = BotoConnectionIssue(
                                str(e), self.index, account, region.name)
                            self.slurp_exception(
                                (self.index, account, region.name), exc, exception_map)
                        continue
                    app.logger.debug("Found {} {}.".format(
                        len(config_recorders), self.i_am_plural))

                    for recorder in config_recorders:
                        name = recorder.get('name')

                        if self.check_ignore_list(name):
                            continue

                        item_config = {
                            'name': name,
                            'role_arn': recorder.get('roleARN'),
                            'recording_group': recorder.get('recordingGroup')
                        }

                        item = ConfigRecorderItem(
                            region=region.name, account=account, name=name, config=item_config)
                        item_list.append(item)

        return item_list, exception_map


class ConfigRecorderItem(ChangeItem):

    def __init__(self, account=None, region=None, name=None, config={}):
        super(ConfigRecorderItem, self).__init__(
            index=ConfigRecorder.index,
            region=region,
            account=account,
            name=name,
            new_config=config)
