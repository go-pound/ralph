import decimal

import boto3
from botocore.exceptions import ClientError


class AwsClient:
    AWS_REGION = "us-east-1"
    DYNAMO_TABLE_NAME = "ralph"

    def __init__(self):
        self.table = boto3.resource("dynamodb", region_name=self.AWS_REGION).Table(self.DYNAMO_TABLE_NAME)

    def put_label(self, user: str, timestamp: decimal, label: str):
        print(f"adding label: user={user} label={label} timestamp={timestamp}")
        try:
            self.table.update_item(
                Key={
                    "type": "label",
                    "target": user
                },
                UpdateExpression="SET labels = list_append(if_not_exists(labels, :empty), :i)",
                ConditionExpression="NOT contains(labels, :i)",
                ExpressionAttributeValues={
                    ":empty": [],
                    ":i": [label]
                }
            )
        except ClientError as e:
            if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
                print("label already exists")

    def delete_label(self, user: str, label: str):
        labels_for_user = self.get_labels_for_user(user)
        index = labels_for_user.index(label) if label in labels_for_user else None

        if index is not None:
            print(f"deleting label: user={user}, label={label}, index={index}")
            query = f"REMOVE labels[{index}]"
            self.table.update_item(
                Key={
                    "type": "label",
                    "target": user
                },
                UpdateExpression=query
            )
        else:
            print(f"no label to delete: user={user}, label={label}")

    def get_labels_for_user(self, user: str) -> list[str]:
        items = self.table.get_item(
            Key={
                "type": "label",
                "target": user
            }
        )["Item"]["labels"]
        print(f"retrieved labels for {user}: {items}")
        return items

    def get_secret(self, secret_name):
        session = boto3.session.Session()
        client = session.client(service_name="secretsmanager", region_name=self.AWS_REGION)
        get_secret_value_response = client.get_secret_value(SecretId=secret_name)

        return get_secret_value_response["SecretString"]
