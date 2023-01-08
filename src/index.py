import json
from app_mention_handler import AppMentionHandler


def lambda_handler(event: json, context: json):
    print(f"Received event: {event} with context {context}")

    body = event['body']['event']
    event_type = body["type"]

    if event_type == "url_verification":
        return url_verification(body)
    elif event_type == "app_mention":
        return AppMentionHandler().respond(body)
    else:
        return {"statusCode": 400, "body": f"Unsupported event type {event_type}"}


def url_verification(body):
    print(f"Responding to challenge: {body}")
    return body["challenge"]
