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
        item_to_delete = next((item for item in labels_for_user if item["label"] == label), None)

        if item_to_delete:
            print(f"deleting label: user={user}, label={label}")
            self.table.delete_item(
                Key={
                    "user": item_to_delete["user"],
                    "timestamp": item_to_delete["timestamp"]
                }
            )
        else:
            print(f"no label to delete: user={user}, label={label}")

    def get_labels_for_user(self, user: str) -> list[map]:
        items = self.table.query(
            KeyConditionExpression=Key("user").eq(user)
        )["Items"]
        print(f"retrieved labels for {user}: {items}")
        return items

    def get_secret(self, secret_name):
        session = boto3.session.Session()
        client = session.client(service_name="secretsmanager", region_name=self.AWS_REGION)
        get_secret_value_response = client.get_secret_value(SecretId=secret_name)

        return get_secret_value_response['SecretString']
