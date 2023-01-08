import decimal

import boto3
from boto3.dynamodb.conditions import Key


class AwsClient:
    AWS_REGION = "us-east-1"
    DYNAMO_TABLE_NAME = 'ralph'

    def __init__(self):
        self.table = boto3.resource("dynamodb", region_name=self.AWS_REGION).Table(self.DYNAMO_TABLE_NAME)

    def put_label(self, user: str, timestamp: decimal, label: str):
        print(f"adding label: user={user} label={label} timestamp={timestamp}")
        self.table.put_item(
            Item={
                "user": user,
                "timestamp": timestamp,
                "label": label
            }
        )

    def delete_label(self, user: str, label: str):
        labels_for_user = self.get_labels_for_user(user)
        item_to_delete = next((lbl for lbl in labels_for_user if lbl == label), None)

        if item_to_delete:
            print(f"deleting label: user={user}, label={label}")
            self.table.delete_item(item_to_delete)
        else:
            print(f"no label to delete: user={user}, label={label}")

    def get_labels_for_user(self, user: str) -> list[map]:
        items = self.table.query(
            KeyConditionExpression=Key("user").eq(user)
        )["Item"]
        print(f"retrieved labels for {user}: {items}")
        return items
