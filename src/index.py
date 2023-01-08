import json

from app_mention_handler import AppMentionHandler


def lambda_handler(event: json, context: json):
    print(f"Received event: {event} with context {context}")

    body = json.loads(event['body']).get('event')
    event_type = body["type"] if body else event['body']['type']  # url_verification events have a different structure

    if event_type == "url_verification":
        return url_verification(event['body'])
    elif event_type == "app_mention":
        return AppMentionHandler().respond(body)
    else:
        return {"statusCode": 400, "body": f"Unsupported event type {event_type}"}


def url_verification(body):
    print(f"Responding to challenge: {body}")
    return body["challenge"]
