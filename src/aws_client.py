"""
Interface for AWS API
"""
import decimal
import logging
import os

import boto3
from botocore.exceptions import ClientError


class AwsClient:
    """Manages AWS connections and API usage."""

    def __init__(self):
        self.region = os.getenv("REGION")
        self.table_name = os.getenv("DYNAMO_TABLE_NAME")
        self.table = boto3.resource("dynamodb", region_name=self.region).Table(self.table_name)

    def put_label(self, user: str, timestamp: decimal, label: str) -> bool:
        """Store a label in DynamoDB."""
        logging.info("adding label: user=%s label=%s timestamp=%s", user, label, timestamp)
        try:
            self.table.update_item(
                Key={
                    "type": "label",
                    "target": user
                },
                UpdateExpression="SET labels = "
                                 "list_append(if_not_exists(labels, :empty), :label_list)",
                ConditionExpression="NOT contains(labels, :label)",
                ExpressionAttributeValues={
                    ":empty": [],
                    ":label_list": [label],
                    ":label": label
                }
            )
            return True
        except ClientError as error:
            if error.response['Error']['Code'] == 'ConditionalCheckFailedException':
                logging.info("label already exists")
                return False
            raise error

    def delete_label(self, user: str, label: str) -> bool:
        """Remove a label from DynamoDB."""
        labels_for_user = self.get_labels_for_user(user)
        index = labels_for_user.index(label) if label in labels_for_user else None

        if index is not None:
            logging.info("deleting label: user=%s, label=%s, index=%s", user, label, index)
            query = f"REMOVE labels[{index}]"
            self.table.update_item(
                Key={
                    "type": "label",
                    "target": user
                },
                UpdateExpression=query
            )
            return True

        logging.info("no label to delete: user=%s, label=%s", user, label)
        return False

    def get_labels_for_user(self, user: str) -> list[str]:
        """Query DynamoDB for a user's labels."""
        result = self.table.get_item(
            Key={
                "type": "label",
                "target": user
            }
        )

        if result.get("Item"):
            labels = result["Item"]["labels"]
            logging.info("retrieved labels for %s: %s", user, labels)
            return labels

        logging.info("no labels for %s", user)
        return []

    def increment_karma(self, target: str, change: int) -> int:
        """Update a karma score."""
        result = self.table.update_item(
            Key={
                "type": "karma",
                "target": target
            },
            UpdateExpression="ADD karma :val",
            ExpressionAttributeValues={
                ":val": change
            },
            ReturnValues="UPDATED_NEW"
        )

        return result["Attributes"]["karma"]

    def list_all_karma(self) -> list[tuple[str, int]]:
        """Get all karma scores in the DB."""
        result = self.table.query(
            KeyConditionExpression="#T = :k",
            ExpressionAttributeNames={
                "#T": "type"
            },
            ExpressionAttributeValues={
                ":k": "karma"
            }
        )["Items"]

        return sorted([(item["target"], item["karma"]) for item in result], key=lambda i: i[1])
