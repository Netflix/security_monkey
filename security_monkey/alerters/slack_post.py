# Houses functions used to compose slack messages to send to Slack
#
# Changes in here will directly affect what messages you receive in slack
#

from slackclient import SlackClient
import os
import json
import requests

SLACK_TOKEN = ''
SLACK_CHANNEL = ''
SLACKBOT_USERNAME = ''

def slack_config_exists():
    SLACK_TOKEN = os.environ.get('SLACK_API_TOKEN')

    if SLACK_TOKEN == 'None':
        return False

    return True

def set_slack_vars():
    SLACK_TOKEN = os.environ.get('SLACK_API_TOKEN')
    SLACK_CHANNEL = os.environ.get('SLACK_CHANNEL')
    SLACKBOT_USERNAME = os.environ.get('SLACKBOT_USERNAME')
    sc = SlackClient(SLACK_TOKEN)
    return sc

def postMessage(attachment, type, tech, name):

    # If the slack client has not been set up yet.
    if slack_config_exits() and SLACK_CHANNEL == '':
        sc = set_slack_vars()
        
    sc.api_call(
        "chat.postMessage",
        channel=SLACK_CHANNEL,
        attachments=[
            {
            "fallback": "New Security Monkey Notification!",
            "color": "#36a64f",
            "title": type
                        },
                        {
            "author_name": "TEST AUTHOR",
            "title": "NAME OF YOUR TITLE LINK",
                        "title_link": "https://SECURITYMONKEYURL/#/items/-/" + tech + "/-/-/" + name + "/-/-/-/-/-/1/25" #CHANGE THIS TO YOUR WEBHOOK FOR YOUR UI TO LINK TO YOUR ITEM PAGE OF THE ITEM IN SCOPE
                        },
                        {
            "text": attachment
                }
        ],
        as_user = True,
        username=SLACKBOT_USERNAME,
        unfurl_links = 'true',
        unfurl_media = 'true'
        )
