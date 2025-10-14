#Entry Lambda that receives user text → stores → classifies → gets Bedrock reply.

# Entry Lambda that receives user text → stores → classifies → gets Bedrock reply → updates vector memory

import json
import os
import boto3
from datetime import datetime
from classify_state import classify_user_state
from respond_nudge import generate_nudge

# Initialize AWS clients
dynamodb = boto3.resource("dynamodb")
lambda_client = boto3.client("lambda")

# Environment variables
TABLE_NAME = os.environ.get("TABLE_NAME", "SainiCheckins")
MEMORY_FUNCTION = os.environ.get("MEMORY_FUNCTION", "update_memory")

def lambda_handler(event, context):
    body = json.loads(event.get("body", "{}"))
    user_id = body.get("user_id")
    message = body.get("message")

    if not user_id or not message:
        return {
            "statusCode": 400,
            "body": json.dumps({"error": "Missing user_id or message"})
        }

    # 1️⃣ Classify emotional tier
    tier = classify_user_state(message)

    # 2️⃣ Generate supportive nudge
    reply = generate_nudge(tier, message)

    # 3️⃣ Store interaction in DynamoDB
    table = dynamodb.Table(TABLE_NAME)
    table.put_item(
        Item={
            "user_id": user_id,
            "timestamp": datetime.utcnow().isoformat(),
            "message": message,
            "tier": tier,
            "response": reply
        }
    )

    # 4️⃣ Asynchronously trigger vector memory update
    try:
        lambda_client.invoke(
            FunctionName=MEMORY_FUNCTION,
            InvocationType="Event",  # async = non-blocking
            Payload=json.dumps({
                "body": json.dumps({
                    "user_id": user_id,
                    "message": message,
                    "tier": tier,
                    "response": reply
                })
            })
        )
    except Exception as e:
        print(f"⚠️ Memory Lambda invocation failed: {e}")

    # 5️⃣ Return response to API Gateway
    return {
        "statusCode": 200,
        "body": json.dumps({
            "tier": tier,
            "response": reply,
            "message": "Check-in logged and memory update triggered."
        })
    }
