import boto3
import json
import os
from datetime import datetime

# ===== AWS CONFIGURATION =====
REGION_CLAUDE = "us-east-1"   # this Lambda runs here
TABLE_REGION = "us-east-2"    # DynamoDB lives here

# Clients
bedrock = boto3.client("bedrock-runtime", region_name=REGION_CLAUDE)
dynamodb = boto3.resource("dynamodb", region_name=TABLE_REGION)

# Table
TABLE_NAME = os.getenv("TABLE_NAME", "SainiCheckins")
table = dynamodb.Table(TABLE_NAME)

MODEL_ID = "anthropic.claude-3-sonnet-20240229-v1:0"


def generate_reflection(message: str, tier: str):
    """Generate a trauma-informed reflection using Claude 3 Sonnet."""
    prompt = f"""
You are Saini, an emotionally intelligent and trauma-informed AI guide.

User emotional tier: {tier}
User message: "{message}"

Respond with one short empathetic reflection (1–2 sentences) that feels calm,
grounded, and supportive. Avoid therapy or medical advice.
Also provide a one-word tone tag (gentle, reassuring, reflective, empowering).
Respond in JSON as:
{{"response": "...", "tone": "..."}}"""

    body = {
        "modelId": MODEL_ID,
        "contentType": "application/json",
        "accept": "application/json",
        "body": json.dumps({
            "inputText": prompt,
            "textGenerationConfig": {"temperature": 0.7, "maxTokenCount": 300}
        }),
    }

    try:
        result = bedrock.invoke_model(
            modelId=MODEL_ID,
            body=json.dumps({
                "inputText": prompt,
                "textGenerationConfig": {"temperature": 0.7, "maxTokenCount": 300},
            }),
            contentType="application/json",
            accept="application/json",
        )
        output = json.loads(result["body"].read())
        # Claude responses vary by schema; handle both
        text = output.get("outputText") or output.get("results", [{}])[0].get("outputText", "")
        parsed = {}
        try:
            parsed = json.loads(text)
        except Exception:
            # fallback if Claude returned plain text
            parsed = {"response": text.strip(), "tone": "gentle"}
        return parsed

    except Exception as e:
        print(f"❌ Claude generation failed: {e}")
        return {
            "response": "I'm here with you; it's okay to take a pause—your feelings matter.",
            "tone": "gentle",
        }


def lambda_handler(event, context):
    try:
        if "body" in event and isinstance(event["body"], str):
            body = json.loads(event["body"])
        else:
            body = event

        user_id = body.get("user_id", "user123")
        tier = body.get("tier", "Stable")
        message = body.get("message", "No message provided.")

        print(f"[Claude us-east-1] Generating reflection for {user_id}...")

        reflection = generate_reflection(message, tier)
        response_text = reflection.get("response", "")
        tone = reflection.get("tone", "gentle")

        # Save record to us-east-2 DynamoDB
        try:
            item = {
                "user_id": user_id,
                "timestamp": datetime.utcnow().isoformat(),
                "message": message,
                "tier": tier,
                "response": response_text,
                "tone": tone,
                "source": "Claude3-Sonnet (us-east-1)"
            }
            table.put_item(Item=item)
            print(f"✅ Stored reflection for {user_id} ({tone})")
        except Exception as db_err:
            print(f"⚠️ DynamoDB write failed: {db_err}")

        return {
            "statusCode": 200,
            "body": json.dumps({
                "response": response_text,
                "tone": tone
            }),
        }

    except Exception as e:
        print(f"❌ Lambda failed: {e}")
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }
