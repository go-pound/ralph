import decimal
import logging

import boto3
from botocore.exceptions import ClientError


class AwsClient:
    AWS_REGION = "us-east-1"
    DYNAMO_TABLE_NAME = "ralph"

    def __init__(self):
        self.table = boto3.resource("dynamodb", region_name=self.AWS_REGION).Table(self.DYNAMO_TABLE_NAME)

    def put_label(self, user: str, timestamp: decimal, label: str) -> bool:
        logging.info(f"adding label: user={user} label={label} timestamp={timestamp}")
        try:
            self.table.update_item(
                Key={
                    "type": "label",
                    "target": user
                },
                UpdateExpression="SET labels = list_append(if_not_exists(labels, :empty), :label_list)",
                ConditionExpression="NOT contains(labels, :label)",
                ExpressionAttributeValues={
                    ":empty": [],
                    ":label_list": [label],
                    ":label": label
                }
            )
            return True
        except ClientError as e:
            if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
                logging.info("label already exists")
                return False
            else:
                raise e

    def delete_label(self, user: str, label: str) -> bool:
        labels_for_user = self.get_labels_for_user(user)
        index = labels_for_user.index(label) if label in labels_for_user else None

        if index is not None:
            logging.info(f"deleting label: user={user}, label={label}, index={index}")
            query = f"REMOVE labels[{index}]"
            self.table.update_item(
                Key={
                    "type": "label",
                    "target": user
                },
                UpdateExpression=query
            )
            return True
        else:
            logging.info(f"no label to delete: user={user}, label={label}")
            return False

    def get_labels_for_user(self, user: str) -> list[str]:
        result = self.table.get_item(
            Key={
                "type": "label",
                "target": user
            }
        )

        if result.get("Item"):
            labels = result["Item"]["labels"]
            logging.info(f"retrieved labels for {user}: {labels}")
            return labels
        else:
            logging.info(f"no labels for {user}")
            return []

    def get_secret(self, secret_name: str) -> str:
        session = boto3.session.Session()
        client = session.client(service_name="secretsmanager", region_name=self.AWS_REGION)
        get_secret_value_response = client.get_secret_value(SecretId=secret_name)

        return get_secret_value_response["SecretString"]
