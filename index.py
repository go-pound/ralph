import json


def lambda_handler(event, context):
    print(f"Received event: {event} with context {context}")

    body = json.loads(event["body"])
    event_type = body["type"]

    if event_type == "url_verification":
        return url_verification(body)
    else:
        return {"statusCode": 400, "body": f"Unsupported event type {event_type}"}


def url_verification(body):
    return body["challenge"]
