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
.. module: security_monkey.watchers.config
    :platform: Unix

.. version:: $$VERSION$$
.. moduleauthor:: Bridgewater OSS <opensource@bwater.com>


"""
from security_monkey.watcher import Watcher
from security_monkey.watcher import ChangeItem
from security_monkey.constants import TROUBLE_REGIONS
from security_monkey.exceptions import BotoConnectionIssue
from security_monkey import app, AWS_DEFAULT_REGION
from boto.rds import regions

AVAILABLE_REGIONS = [AWS_DEFAULT_REGION]


class Config(Watcher):
    index = 'config'
    i_am_singular = 'Config'
    i_am_plural = 'Config'

    def __init__(self, accounts=None, debug=False):
        super(Config, self).__init__(accounts=accounts, debug=debug)

    def slurp(self):
        """
        :returns: item_list - list of configs.
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
                if region.name not in AVAILABLE_REGIONS:
                    continue

                try:
                    configService = connect(
                        account, 'boto3.config.client', region=region)
                    app.logger.debug(
                        "Config policy is: {}".format(configService))
                    response = self.wrap_aws_rate_limited_call(
                        configService.describe_config_rules
                    )
                    config_rules = response.get('ConfigRules', [])
                except Exception as e:
                    app.logger.debug("Exception found: {}".format(e))
                    if region.name not in TROUBLE_REGIONS:
                        exc = BotoConnectionIssue(
                            str(e), self.index, account, region.name)
                        self.slurp_exception(
                            (self.index, account, region.name), exc, exception_map)
                    continue
                app.logger.debug("Found {} {}.".format(
                    len(config_rules), self.i_am_plural))

                for config_rule in config_rules:
                    name = config_rule.get('ConfigRuleName')

                    if self.check_ignore_list(name):
                        continue

                    item_config = {
                        'config_rule': name,
                        'config_rule_arn': config_rule.get('ConfigRuleArn'),
                        'config_rule_id': config_rule.get('ConfigRuleId'),
                        'scope': config_rule.get('Scope', {}),
                        'source': config_rule.get('Source', {}),
                        'imput_parameters': config_rule.get('InputParameters'),
                        'maximum_execution_frequency': config_rule.get('MaximumExecutionFrequency'),
                        'config_rule_state': config_rule.get('ConfigRuleState'),
                    }

                    item = ConfigItem(
                        region=region.name, account=account, name=name,
                        arn=config_rule.get('ConfigRuleArn'), config=item_config,
                        source_watcher=self)
                    item_list.append(item)

        return item_list, exception_map


class ConfigItem(ChangeItem):

    def __init__(self, account=None, region=None, name=None, arn=None, config=None, source_watcher=None):
        super(ConfigItem, self).__init__(
            index=Config.index,
            region=region,
            account=account,
            name=name,
            arn=arn,
            new_config=config if config else {},
            source_watcher=source_watcher
        )
