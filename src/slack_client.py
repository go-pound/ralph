import decimal
import json
import urllib.parse
import urllib.request

from aws_client import AwsClient


class SlackClient:
    ADD_REACTION_URL = "https://slack.com/api/reactions.add"
    POST_MESSAGE_URL = "https://slack.com/api/chat.postMessage"
    SLACK_TOKEN_SECRET_NAME = "ralph_slack_token"

    token = None

    def __init__(self):
        self.aws_client = AwsClient()

    def add_reaction(self, reaction_name: str, channel: str, timestamp: decimal):
        payload = {
            "channel": channel,
            "name": reaction_name,
            "timestamp": timestamp
        }
        self.post(self.ADD_REACTION_URL, payload)

    def reply_in_thread(self, text: str, channel: str, timestamp: decimal):
        payload = {
            "channel": channel,
            "thread_ts": timestamp,
            "text": text
        }
        self.post(self.POST_MESSAGE_URL, payload)

    def post(self, url: str, payload: dict):
        body = urllib.parse.urlencode(payload).encode("utf-8")
        print(f"Sending request to {url}: {payload}")
        request = urllib.request.Request(url, headers=self.headers(), data=body)
        with open(urllib.request.urlopen(request)) as response:
            print(f"Received response: {response}")

    def headers(self):
        token = self.token or json.loads(self.aws_client.get_secret(self.SLACK_TOKEN_SECRET_NAME))["token"]
        self.token = token
        return {
            "Authorization": f"Bearer {token}"
        }
