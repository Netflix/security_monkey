"""alert slack with any auditor"""

import json

import requests
from security_monkey import app


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
