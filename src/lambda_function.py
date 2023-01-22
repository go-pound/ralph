import json
import logging
import os

from app_mention_handler import AppMentionHandler


def lambda_handler(event: json, context: json):
    log_level = os.getenv("LOG_LEVEL", "WARN")
    logging.getLogger().setLevel(log_level)

    logging.info("Received event: %s with context %s", event, context)

    body = json.loads(event['body'])
    event = body.get('event')
    # url_verification events have a different structure
    event_type = event["type"] if event else body["type"]

    if event_type == "url_verification":
        logging.info("Responding to challenge: %s", body)
        return body["challenge"]

    if event_type == "app_mention":
        return AppMentionHandler().respond(event)

    return {"statusCode": 400, "body": f"Unsupported event type {event_type}"}
