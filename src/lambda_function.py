import json
import logging
import os

from app_mention_handler import AppMentionHandler


def lambda_handler(event: json, context: json):
    log_level = os.getenv("LOG_LEVEL", logging.WARN)
    logging.getLogger().setLevel(log_level)

    logging.info(f"Received event: {event} with context {context}")

    body = json.loads(event['body'])
    event = body.get('event')
    event_type = event["type"] if event else body["type"]  # url_verification events have a different structure

    if event_type == "url_verification":
        logging.info(f"Responding to challenge: {body}")
        return body["challenge"]
    elif event_type == "app_mention":
        return AppMentionHandler().respond(event)
    else:
        return {"statusCode": 400, "body": f"Unsupported event type {event_type}"}
