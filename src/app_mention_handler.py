import html
import json
import logging
import re
import decimal

from aws_client import AwsClient
from slack_client import SlackClient


class AppMentionHandler:
    label_regex = re.compile(
        "<@[A-Z0-9]+> (?P<user><@[A-Z0-9]+>) (?P<verb>is not|is|<<|>>) (?P<label>.+)"
    )
    label_whois_regex = re.compile(
        "<@[A-Z0-9]+> who is (?P<user><@[A-Z0-9]+>)"
    )

    def __init__(self):
        self.aws_client = AwsClient()
        self.slack_client = SlackClient()

    def respond(self, event: json):
        message = html.unescape(event["text"])
        channel = event["channel"]
        timestamp = decimal.Decimal(event["event_ts"])

        try:
            if self.label_regex.match(message):
                self.handle_label_message(message, channel, timestamp)
            elif self.label_whois_regex.match(message):
                self.handle_label_whois_message(message, channel, timestamp)
            else:
                logging.info(f"Unhandled message {message}")
                self.slack_client.add_reaction("question", channel, timestamp)
        except Exception as e:
            self.slack_client.add_reaction("x", channel, timestamp)
            raise e

    def handle_label_whois_message(self, message: str, channel: str, timestamp: decimal):
        match = self.label_whois_regex.match(message)
        user = match.group("user")
        labels = self.aws_client.get_labels_for_user(user)
        if labels:
            text = f"{user} is {', '.join(labels)}"
            self.slack_client.reply_in_thread(text, channel, timestamp)
        else:
            self.slack_client.reply_in_thread(f"{user}? Never heard of 'em", channel, timestamp)

    def handle_label_message(self, message: str, channel: str, timestamp: decimal):
        match = self.label_regex.match(message)

        user = match.group("user")
        verb = match.group("verb")
        label = match.group("label")

        logging.info(f"handling label message: user={user}, verb={verb}, label={label}")

        if verb == "is" or verb == "<<":
            self.aws_client.put_label(user, timestamp, label) or \
                self.slack_client.reply_in_thread("I know", channel, timestamp)
        else:
            self.aws_client.delete_label(user, label) or \
                self.slack_client.reply_in_thread("I know", channel, timestamp)

        self.slack_client.add_reaction("white_check_mark", channel, timestamp)
