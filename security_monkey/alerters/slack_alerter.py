"""alert slack with any auditor"""

import json

import requests
from security_monkey import app
from security_monkey.alerters import custom_alerter

alerter_registry = []
slack_config = {}
slack_hook = ""


class SlackAlerter(object):
    __metaclass__ = custom_alerter.AlerterType

    if app.config.get('SLACK_HOOK'):

        slack_config = {
            'channel': app.config.get('SLACK_CHANNEL'),
            'username': app.config.get('SLACK_USERNAME'),
            'icon_emoji': app.config.get('SLACK_ICON'),
        }

        slack_hook = app.config.get('SLACK_HOOK')

        slack_config['attachments'] = []

    def report_auditor_changes(self, auditor):
        for item in auditor.items:
            for issue in item.confirmed_new_issues:
                x = {
                    'text': "New Issue: Index: {!s}\n Account: {!s}\n Region: {!s}\n Name: {!s}".format(item.index, item.account, item.region, item.name)
                }

                slack_config['attachments'].append(x)
                try:
                    requests.post(slack_hook, data=json.dumps(slack_config))
                    slack_config['attachments'] = []

                except Exception as e:
                    print("something has gone wrong with the slack post. Please check your configuration. " + e)
