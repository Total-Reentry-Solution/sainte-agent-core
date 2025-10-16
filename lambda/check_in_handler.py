import json
import boto3
import os
from datetime import datetime

# ===== AWS CONFIGURATION =====
REGION_LOCAL = "us-east-2"          # main region (Lambda + DynamoDB)
REGION_REMOTE = "us-east-1"         # Claude model region

# Clients
bedrock = boto3.client("bedrock-runtime", region_name=REGION_LOCAL)
lambda_client = boto3.client("lambda", region_name=REGION_REMOTE)
dynamodb = boto3.resource("dynamodb", region_name=REGION_LOCAL)

# Tables
TABLE_NAME = os.getenv("TABLE_NAME", "SainiCheckins")
table = dynamodb.Table(TABLE_NAME)


def lambda_handler(event, context):
    try:
        # --- Parse event body ---
        if "body" in event and isinstance(event["body"], str):
            body = json.loads(event["body"])
        else:
            body = event

        user_id = body.get("user_id", "user123")
        tier = body.get("tier", "At-Risk")
        message = body.get("message", "No message provided.")

        print(f"[Check-In] Received from {user_id}: {message} (Tier={tier})")

        # --- Build payload for Claude reflection ---
        payload = {
            "body": json.dumps({
                "user_id": user_id,
                "tier": tier,
                "message": message
            })
        }

        # --- Cross-region invoke of Claude reflection (us-east-1) ---
        invoke_response = lambda_client.invoke(
            FunctionName="respond_nudge_us_east_1",
            InvocationType="RequestResponse",
            Payload=json.dumps(payload)
        )

        result = json.loads(invoke_response["Payload"].read())
        body_result = json.loads(result.get("body", "{}"))
        reflection = body_result.get("response") or body_result.get("nudge", "")
        tone = body_result.get("tone", "neutral")

        print(f"[Claude Reflection] => {reflection} (tone={tone})")

        # --- Store to DynamoDB ---
        try:
            item = {
                "user_id": user_id,
                "timestamp": datetime.utcnow().isoformat(),
                "message": message,
                "tier": tier,
                "response": reflection,
                "tone": tone,
                "source": "Claude-via-us-east-1"
            }
            table.put_item(Item=item)
            print(f"✅ Stored check-in for {user_id}")
        except Exception as db_err:
            print(f"⚠️ DynamoDB write failed: {db_err}")

        # --- Return to caller ---
        return {
            "statusCode": 200,
            "body": json.dumps({
                "user_id": user_id,
                "tier": tier,
                "nudge": reflection or "No reflection generated.",
                "tone": tone
            }),
        }

    except Exception as e:
        print(f"❌ Error in check_in_handler: {e}")
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }
