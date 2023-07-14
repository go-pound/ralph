"""
Respond to incoming Slack messages mentioning Ralph.
"""
import html
import json
import logging
import random
import re
import decimal
import xml.etree.ElementTree as et
import requests

from aws_client import AwsClient
from slack_client import SlackClient


def generate_karma_response(target: str, change: int, new_total: int) -> str:
    """Generate a response for when a karma score is updated."""
    positive_messages = [
        "is on the rise!",
        "leveled up!",
        ":chart_with_upwards_trend:"
    ]
    negative_messages = [
        "took a hit!",
        ":chart_with_downwards_trend:"
    ]

    description = random.choice(positive_messages if change > 0 else negative_messages)
    return f"{target} {description} (total: {new_total})"


def generate_leaderboard_response(leaderboard_type: str, karma: list[tuple[str, int]], count: int):
    """Generate a response when asked for the highest or lowest karma scores."""
    data = karma[-1:-count-1:-1] if leaderboard_type == "best" else karma[:count]
    intro = f"{leaderboard_type.capitalize()} all time:"
    scores = "\n".join([f"{i + 1}. {item[0]} ({item[1]})" for i, item in enumerate(data)])
    return f"{intro}\n{scores}"


class AppMentionHandler:
    """Process incoming Slack messages."""
    french_toast_regex = re.compile(
        "<@[A-Z0-9]+> french\\s?toast",
        re.IGNORECASE
    )
    karma_leaderboard_regex = re.compile(
        "<@[A-Z0-9]+> karma (?P<type>best|worst)"
    )
    karma_regex = re.compile(
        r"<@[A-Z0-9]+> (?P<target>\S+)(?P<sign>\+\+|--)"
    )
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
        """Parse an event and delegate its message to its respective handler."""
        message = html.unescape(event["text"])
        channel = event["channel"]
        timestamp = decimal.Decimal(event["event_ts"])

        try:
            if self.french_toast_regex.match(message):
                self.handle_french_toast_alert(message, channel, timestamp)
            elif self.karma_leaderboard_regex.match(message):
                self.handle_karma_leaderboard_message(message, channel, timestamp)
            elif self.karma_regex.match(message):
                self.handle_karma_message(message, channel, timestamp)
            elif self.label_regex.match(message):
                self.handle_label_message(message, channel, timestamp)
            elif self.label_whois_regex.match(message):
                self.handle_label_whois_message(message, channel, timestamp)
            else:
                logging.info("Unhandled message %s", message)
                self.slack_client.add_reaction("question", channel, timestamp)
        except Exception as error:
            self.slack_client.add_reaction("x", channel, timestamp)
            raise error

    def handle_french_toast_alert(self, message: str, channel: str, timestamp: decimal):
        """Respond when asked for the current French Toast Alert level."""
        req = requests.get('https://universalhub.com/toast.xml', timeout=10)
        root = et.fromstring(req.text)
        alert_level = root.find('status').text
        message = f"The UniversalHub French Toast alert level is: {alert_level}"
        self.slack_client.reply_in_thread(message, channel, timestamp)

    def handle_karma_leaderboard_message(self, message: str, channel: str, timestamp: decimal):
        """Respond when asked for the top or bottom karma scores."""
        match = self.karma_leaderboard_regex.match(message)

        leaderboard_type = match.group("type")
        all_karma = self.aws_client.list_all_karma()
        message = generate_leaderboard_response(leaderboard_type, all_karma, 10)
        self.slack_client.reply_in_thread(message, channel, timestamp)

    def handle_karma_message(self, message: str, channel: str, timestamp: decimal):
        """Respond when asked to update a karma score."""
        match = self.karma_regex.match(message)

        target = match.group("target")
        change = 1 if match.group("sign") == "++" else -1

        new_total = self.aws_client.increment_karma(target, change)
        message = generate_karma_response(target, change, new_total)

        self.slack_client.reply_in_thread(message, channel, timestamp)

    def handle_label_whois_message(self, message: str, channel: str, timestamp: decimal):
        """Respond with the labels for a user."""
        match = self.label_whois_regex.match(message)
        user = match.group("user")
        labels = self.aws_client.get_labels_for_user(user)
        if labels:
            text = f"{user} is {', '.join(labels)}"
            self.slack_client.reply_in_thread(text, channel, timestamp)
        else:
            self.slack_client.reply_in_thread(f"{user}? Never heard of 'em", channel, timestamp)

    def handle_label_message(self, message: str, channel: str, timestamp: decimal):
        """Update the label list for a user."""
        match = self.label_regex.match(message)

        user = match.group("user")
        verb = match.group("verb")
        label = match.group("label")

        logging.info("handling label message: user=%s, verb=%s, label=%s", user, verb, label)

        if verb in ("is", "<<") and not self.aws_client.put_label(user, timestamp, label):
            self.slack_client.reply_in_thread("I know", channel, timestamp)
        elif verb in ("is not", ">>") and not self.aws_client.delete_label(user, label):
            self.slack_client.reply_in_thread("I know", channel, timestamp)

        self.slack_client.add_reaction("white_check_mark", channel, timestamp)
