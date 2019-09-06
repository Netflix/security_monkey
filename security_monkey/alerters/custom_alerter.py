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
.. module: security_monkey.alerters.custom_alerter
    :platform: Unix

.. version:: $$VERSION$$
.. moduleauthor:: Bridgewater OSS <opensource@bwater.com>


"""
import json

import requests
from security_monkey import app

alerter_registry = []


class AlerterType(type):

    def __init__(cls, name, bases, attrs):
        if getattr(cls, "report_auditor_changes", None) and getattr(cls, "report_watcher_changes", None):
            app.logger.debug("Registering alerter %s", cls.__name__)
            alerter_registry.append(cls)


def report_auditor_changes(auditor):
    for alerter_class in alerter_registry:
        alerter = alerter_class()
        alerter.report_auditor_changes(auditor)
        if app.config.get('SLACK_HOOK'):
            alert_slack(auditor)


def report_watcher_changes(watcher):
    for alerter_class in alerter_registry:
        alerter = alerter_class()
        alerter.report_watcher_changes(watcher)


def alert_slack(auditor):
    # using requests to post issue to slack if configured.
    slack_config = {
        'channel': app.config.get('SLACK_CHANNEL'),
        'username': app.config.get('SLACK_USERNAME'),
        'icon_emoji': app.config.get('SLACK_ICON'),
    }

    slack_hook = app.config.get('SLACK_HOOK')

    slack_config['attachments'] = []

    for item in auditor.items:
        for issue in item.confirmed_new_issues:
            x = {
                'text': "New Issue: Index: {!s}\n Account: {!s}\n Region: {!s}\n Name: {!s}".format(item.index, item.account, item.region, item.name)
            }

            slack_config['attachments'].append(x)
            slack_post(slack_config, slack_hook)


def slack_post(slack_config, slack_hook):
    try:
        requests.post(slack_hook, data=json.dumps(slack_config))
    except Exception as e:
        print("something has gone wrong with the slack post. Please check your configuration. " + e)
