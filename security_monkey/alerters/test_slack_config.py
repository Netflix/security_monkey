# test the connection to slack

from custom_alerter import slack_post
from security_monkey import app

slack_config = {
        'channel': app.config.get('SLACK_CHANNEL'),
        'username': app.config.get('SLACK_USERNAME'),
        'icon_emoji': app.config.get('SLACK_ICON'),
    }

slack_hook = app.config.get('SLACK_HOOK')

x = {
    "text": "Slack is Successfully hooked up to Security Monkey"
}
slack_config['attachments'].append(x)

slack_post(slack_config, slack_hook)
