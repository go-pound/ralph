import json
import urllib.parse
import urllib.request

from aws_client import AwsClient


class SlackClient:
    POST_MESSAGE_URL = "https://slack.com/api/chat.postMessage"
    SLACK_TOKEN_SECRET_NAME = "ralph_slack_token"

    def __init__(self):
        self.aws_client = AwsClient()

    def reply_in_thread(self, text, channel, timestamp):
        token = json.loads(self.aws_client.get_secret(self.SLACK_TOKEN_SECRET_NAME))["token"]
        headers = {
            "Authorization": f"Bearer {token}"
        }
        payload = urllib.parse.urlencode({
            "channel": channel,
            "thread_ts": timestamp,
            "text": text
        })
        print(f"Sending Slack message: {payload}")
        request = urllib.request.Request(self.POST_MESSAGE_URL, headers=headers, data=payload.encode("utf-8"))
        response = urllib.request.urlopen(request).read()
        print(f"Received response: {response}")
