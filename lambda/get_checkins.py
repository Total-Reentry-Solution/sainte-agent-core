import boto3
import json
import os

dynamodb = boto3.resource("dynamodb")
TABLE_NAME = os.environ.get("TABLE_NAME", "SainiCheckins")
table = dynamodb.Table(TABLE_NAME)

def lambda_handler(event, context):
    try:
        response = table.scan()
        items = response.get("Items", [])
        return {
            "statusCode": 200,
            "headers": {
                "Access-Control-Allow-Origin": "*",
                "Content-Type": "application/json"
            },
            "body": json.dumps(items)
        }
    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }
