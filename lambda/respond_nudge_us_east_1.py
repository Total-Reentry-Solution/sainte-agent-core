import boto3, json, os
from datetime import datetime

# ===== REGIONS =====
REGION_CLAUDE = "us-east-1"
TABLE_REGION = "us-east-2"

bedrock = boto3.client("bedrock-runtime", region_name=REGION_CLAUDE)
dynamodb = boto3.resource("dynamodb", region_name=TABLE_REGION)
table = dynamodb.Table(os.getenv("TABLE_NAME", "SainiCheckins"))

MODEL_ID = "anthropic.claude-3-sonnet-20240229-v1:0"


def fetch_recent_context(user_id: str, limit: int = 3):
    """Fetch last few check-ins for conversation context."""
    try:
        resp = table.scan()
        items = [i for i in resp.get("Items", []) if i.get("user_id") == user_id]
        items.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        return items[:limit]
    except Exception as e:
        print(f"⚠️ Context fetch failed: {e}")
        return []


def generate_conversation(message: str, tier: str, context_msgs):
    """Generate empathetic conversational reply using Claude 3 Sonnet (native schema)."""
    messages = []

    # Append short context (conversation memory)
    for item in reversed(context_msgs):
        messages.append({"role": "user", "content": item.get("message", "")})
        messages.append({"role": "assistant", "content": item.get("response", "")})

    # Add current message
    messages.append({
        "role": "user",
        "content": f"User emotional tier: {tier}\nUser says: {message}"
    })

    # ✅ Native Anthropic request structure per AWS docs
    payload = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 400,
        "temperature": 0.7,
        "messages": messages
    }

    try:
        response = bedrock.invoke_model(
            modelId=MODEL_ID,
            body=json.dumps(payload),
            contentType="application/json",
            accept="application/json"
        )

        raw = json.loads(response["body"].read())
        content_list = raw.get("content", [])
        text = content_list[0].get("text", "") if content_list else ""

        return {"response": text.strip(), "tone": "gentle"}

    except Exception as e:
        print(f"❌ Claude generation failed: {e}")
        return {
            "response": "I’m here with you. Tell me more about how you’re feeling today.",
            "tone": "gentle"
        }


def lambda_handler(event, context):
    try:
        body = json.loads(event["body"]) if "body" in event and isinstance(event["body"], str) else event
        user_id = body.get("user_id", "guest_user")
        tier = body.get("tier", "Stable")
        message = body.get("message", "No message provided.")

        print(f"[Claude Conversation] user={user_id}, tier={tier}")

        context_msgs = fetch_recent_context(user_id)
        reflection = generate_conversation(message, tier, context_msgs)
        response_text = reflection.get("response", "")
        tone = reflection.get("tone", "gentle")

        # Save reflection to DynamoDB
        item = {
            "user_id": user_id,
            "timestamp": datetime.utcnow().isoformat(),
            "message": message,
            "tier": tier,
            "response": response_text,
            "tone": tone,
            "source": "Claude3-Sonnet-Native"
        }
        table.put_item(Item=item)
        print(f"✅ Conversational reply stored for {user_id} ({tone})")

        return {
            "statusCode": 200,
            "body": json.dumps({
                "response": response_text,
                "tone": tone
            })
        }

    except Exception as e:
        print(f"❌ Lambda failed: {e}")
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }
