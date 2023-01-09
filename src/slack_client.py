import decimal
import logging
import os
import urllib.parse
import urllib.request

from aws_client import AwsClient


def headers():
    token = os.getenv("SLACK_API_TOKEN")
    return {
        "Authorization": f"Bearer {token}"
    }


def post(url: str, payload: dict):
    body = urllib.parse.urlencode(payload).encode("utf-8")
    logging.info(f"Sending request to {url}: {payload}")
    request = urllib.request.Request(url, headers=headers(), data=body)
    response = urllib.request.urlopen(request).read()
    logging.info(f"Received response: {response}")


class SlackClient:
    ADD_REACTION_URL = "https://slack.com/api/reactions.add"
    POST_MESSAGE_URL = "https://slack.com/api/chat.postMessage"

    def __init__(self):
        self.aws_client = AwsClient()

    def add_reaction(self, reaction_name: str, channel: str, timestamp: decimal):
        payload = {
            "channel": channel,
            "name": reaction_name,
            "timestamp": timestamp
        }
        post(self.ADD_REACTION_URL, payload)

    def reply_in_thread(self, text: str, channel: str, timestamp: decimal):
        payload = {
            "channel": channel,
            "thread_ts": timestamp,
            "text": text
        }
        post(self.POST_MESSAGE_URL, payload)
