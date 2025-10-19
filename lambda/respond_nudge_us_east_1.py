# lambda/respond_nudge_us_east_1.py
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
    """Fetch the last few check-ins for conversational context."""
    try:
        resp = table.scan()
        items = [i for i in resp.get("Items", []) if i.get("user_id") == user_id]
        items.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        return items[:limit]
    except Exception as e:
        print(f"⚠️ Context fetch failed: {e}")
        return []

def generate_conversation(message: str, tier: str, context_msgs):
    """Generate empathetic conversation reply using Claude 3 Sonnet."""
    history_text = ""
    for i, item in enumerate(context_msgs):
        history_text += f"User({i}): {item.get('message')}\nSaini: {item.get('response')}\n"
    prompt = f"""
You are Saini, an emotionally intelligent and trauma-informed AI companion.
Respond as if continuing a caring conversation.

User emotional tier: {tier}
Conversation history:
{history_text}

User now says: "{message}"

Respond in a tone that matches prior empathy. 
Reply with 2-3 warm, human-like sentences showing understanding and gentle guidance.
Also output a short tone tag (gentle, reflective, reassuring, empowering).

Respond in JSON:
{{"response": "...", "tone": "..."}}"""

    try:
        result = bedrock.invoke_model(
            modelId=MODEL_ID,
            body=json.dumps({
                "inputText": prompt,
                "textGenerationConfig": {"temperature": 0.8, "maxTokenCount": 350},
            }),
            contentType="application/json",
            accept="application/json",
        )
        output = json.loads(result["body"].read())
        text = output.get("outputText") or output.get("results", [{}])[0].get("outputText", "")
        try:
            return json.loads(text)
        except:
            return {"response": text.strip(), "tone": "gentle"}
    except Exception as e:
        print(f"❌ Claude generation failed: {e}")
        return {"response": "I'm here with you. Tell me more about how today feels.", "tone": "gentle"}

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

        item = {
            "user_id": user_id,
            "timestamp": datetime.utcnow().isoformat(),
            "message": message,
            "tier": tier,
            "response": response_text,
            "tone": tone,
            "source": "Claude3-Sonnet-Conversation"
        }
        table.put_item(Item=item)
        print(f"✅ Conversational reply stored for {user_id} ({tone})")

        return {"statusCode": 200, "body": json.dumps({"response": response_text, "tone": tone})}

    except Exception as e:
        print(f"❌ Lambda failed: {e}")
        return {"statusCode": 500, "body": json.dumps({"error": str(e)})}
