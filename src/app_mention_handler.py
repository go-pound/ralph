import json
import re
import decimal

from aws_client import AwsClient


class AppMentionHandler:
    label_regex = re.compile(
        "<@[A-Z0-9]+> (?P<user><@[A-Z0-9]+>) (?P<verb>is not|is|<<|>>) (?P<label>.+)"
    )

    def __init__(self):
        self.aws_client = AwsClient()

    def respond(self, event: json):
        message = event["text"]
        timestamp = decimal.Decimal(event["event_ts"])

        if self.label_regex.fullmatch(message):
            self.handle_label_message(message, timestamp)
        else:
            pass

    def handle_label_message(self, message: str, timestamp: decimal):
        match = self.label_regex.fullmatch(message)

        user = match.group("user")
        verb = match.group("verb")
        label = match.group("label")

        print(f"handling label message: user={user}, verb={verb}, label={label}")

        if verb == "is" or verb == "<<":
            self.aws_client.put_label(user, timestamp, label)
        else:
            self.aws_client.delete_label(user, label)
