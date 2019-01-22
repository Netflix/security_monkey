# Houses functions used to compose slack messages to send to Slack
#
# Changes in here will directly affect what messages you receive in slack
# Date :: June 2018
#

from slackclient import SlackClient
import os
import json
import requests

SLACK_TOKEN = "None"
CHANNEL = "None"
SLACKBOT_USERNAME = "None"
SM_UI_WEBHOOK = "None"

def postMessage(attachment, type, tech, name):

    if os.environ.get("SLACK_API_TOKEN") != "None":
        SLACK_TOKEN = os.environ.get("SLACK_API_TOKEN") # env variable stored in key

    if os.environ.get("SLACK_CHANNEL") != "None":
        CHANNEL = os.environ.get("CHANNEL") # slack channel stored in key

    if os.environ.get("SLACKBOT_USERNAME") != "None":
        SLACKBOT_USERNAME = os.environ.get("SLACKBOT_USERNAME")

    if os.environ.get("SM_UI_WEBHOOK") != "None":
        SM_UI_WEBHOOK = os.environ.get("SM_UI_WEBHOOK")
    sc = SlackClient(SLACK_TOKEN)

    sc.api_call(
        "chat.postMessage",
        channel=CHANNEL,
        attachments=[
            {
            "fallback": "New Security Monkey Notification!",
            "color": "#36a64f",
            "title": type
			},
			{
            "author_name": "Security Monkey",
            "title": "New Security Monkey Notification",
			"title_link": SM_UI_WEBHOOK,
			},
			{
            "text": attachment
           	}
        ],
        as_user = True,
        username='SLACKBOT_USERNAME',
        unfurl_links = 'true',
        unfurl_media = 'true'
        )  
