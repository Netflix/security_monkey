"""alert slack with any auditor"""

import json

import requests
from security_monkey import app
from security_monkey.alerters import custom_alerter


class SlackAlerter(object, metaclass=custom_alerter.AlerterType):
    def __init__(self, cls, name, bases, attrs):
        super().__init__(cls, name, bases, attrs)
        self.slack_config = {}
        self.slack_hook = ""

        if app.config.get('SLACK_HOOK'):

            self.slack_config = {
                'channel': app.config.get('SLACK_CHANNEL'),
                'username': app.config.get('SLACK_USERNAME'),
                'icon_emoji': app.config.get('SLACK_ICON'),
            }

            self.slack_hook = app.config.get('SLACK_HOOK')

    def report_auditor_changes(self, auditor):
        for item in auditor.items:
            for issue in item.confirmed_new_issues:
                x = {
                    'text': "New Issue: Index: {!s}\n Account: {!s}\n Region: {!s}\n Name: {!s}".format(item.index, item.account, item.region, item.name)
                }

                self.slack_config['attachments'] = x

                try:
                    requests.post(self.slack_hook, data=json.dumps(self.slack_config))
                    self.slack_config['attachments'] = []

                except Exception as e:
                    app.logger.exception(e)
                    app.logger.error("something has gone wrong with the slack post. Please check your configuration. " + e)
