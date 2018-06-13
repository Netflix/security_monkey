# Houses functions used to compose slack messages to send to Slack
#
# Changes in here will directly affect what messages you receive in slack
# Written by :: Drew Gallis <drew.gallis@willowtreeapps.com>
# Date :: June 2018
#

from slackclient import SlackClient
import os
import json
import requests


def postMessage(attachment, type, tech, name):

    # Post to slack
    slack_token = os.environ["SLACK_API_TOKEN"] #env variable stored key 
    sc = SlackClient(slack_token)
    channel = 'CHANNEL ID HERE' #test by posting to your own slack channel id, can be changed to any channel

    sc.api_call(
        "chat.postMessage",
        channel=channel,
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
        username='SLACKBOT USERNAME',
        unfurl_links = 'true',
        unfurl_media = 'true'
        )  