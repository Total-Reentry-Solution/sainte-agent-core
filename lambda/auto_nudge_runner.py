import boto3, os, json, datetime
from decimal import Decimal

# Initialize AWS clients
dynamodb = boto3.resource("dynamodb")
checkins_table = dynamodb.Table(os.environ.get("TABLE_NAME", "SainiCheckins"))
bedrock = boto3.client("bedrock-runtime", region_name=os.environ.get("AWS_REGION", "us-east-2"))

def lambda_handler(event, context):
    try:
        # 1️⃣ Find users who haven’t checked in for 2+ days
        all_items = checkins_table.scan()["Items"]
        cutoff = datetime.datetime.utcnow() - datetime.timedelta(days=2)
        inactive_users = {}
        for item in all_items:
            try:
                ts = datetime.datetime.fromisoformat(item["timestamp"])
                if ts < cutoff:
                    inactive_users[item["user_id"]] = item
            except Exception:
                continue

        # 2️⃣ Generate supportive nudges using Bedrock Nova model
        for uid in inactive_users:
            prompt = f"Write a short, supportive daily check-in message for user {uid} who hasn’t checked in for 2 days. Keep it warm, brief, and encouraging."
            body = json.dumps({
                "inputText": prompt,
                "textGenerationConfig": {
                    "temperature": 0.7,
                    "maxTokenCount": 150
                }
            })
            
            try:
                response = bedrock.invoke_model(
                    modelId="amazon.nova-pro-v1:0",
                    body=body,
                    contentType="application/json",
                    accept="application/json"
                )
                result = json.loads(response["body"].read())
                msg = result.get("outputText", "Just checking in gently 💬")
            except Exception as e:
                msg = f"Just checking in gently 💬 (fallback due to {str(e)[:50]})"

            # 3️⃣ Log auto-nudge in DynamoDB
            checkins_table.put_item(Item={
                "user_id": uid,
                "timestamp": datetime.datetime.utcnow().isoformat(),
                "message": "[AUTO] Daily nudge",
                "tier": "Auto",
                "response": msg,
                "is_auto": True
            })

        print(f"[AUTO_NUDGE] Sent nudges to: {list(inactive_users.keys())}")
        return {
            "statusCode": 200,
            "body": json.dumps({
                "nudged_users": list(inactive_users.keys()),
                "count": len(inactive_users)
            })
        }

    except Exception as e:
        print(f"[ERROR] {str(e)}")
        return {"statusCode": 500, "body": json.dumps({"error": str(e)})}
