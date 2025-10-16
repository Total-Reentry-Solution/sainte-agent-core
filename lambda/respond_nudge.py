import os
import json
import boto3

REGION = os.getenv("AWS_REGION", "us-east-2")
bedrock = boto3.client("bedrock-runtime", region_name=REGION)

# --- Models available in us-east-2 ---
PRIMARY_MODEL = "anthropic.claude-3-sonnet-20240229-v1:0"
FALLBACK_MODEL = "cohere.command-r-plus-v1:0"

def generate_reflective_nudge(user_id: str, tier: str, message: str) -> str:
    """Generate an empathetic trauma-informed reflection."""
    prompt = f"""
You are a compassionate trauma-informed AI helper called Sainte.
Your goal is to comfort and validate someone’s emotions with empathy.

User message: {message}
Emotional tier: {tier}

Write one brief, heartfelt reflection (1–2 sentences) that
validates the user's experience and encourages groundedness.
Avoid generic advice or repetition.
"""

    body = {
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 200,
        "temperature": 0.7
    }

    try:
        response = bedrock.invoke_model(
            modelId=PRIMARY_MODEL,
            body=json.dumps(body),
            contentType="application/json",
            accept="application/json"
        )
        result = json.loads(response["body"].read())
        # Anthropic Claude format
        text = result.get("content", [{}])[0].get("text", "")
        if not text:
            text = result.get("completion", "")
        return text.strip()

    except Exception as e:
        print(f"⚠️ Primary model failed ({e}), switching to fallback…")
        try:
            response = bedrock.invoke_model(
                modelId=FALLBACK_MODEL,
                body=json.dumps({
                    "input": prompt,
                    "temperature": 0.7,
                    "max_tokens": 200
                }),
                contentType="application/json",
                accept="application/json"
            )
            result = json.loads(response["body"].read())
            return result.get("text", "").strip() or "I'm here with you; take a slow breath and know you're safe."
        except Exception as inner_e:
            print(f"❌ Fallback failed: {inner_e}")
            return "I'm here with you; it's okay to pause—your feelings matter."

def lambda_handler(event, context):
    body = json.loads(event.get("body", "{}"))
    user_id = body.get("user_id", "guest_user")
    tier = body.get("tier", "At-Risk")
    message = body.get("message", "I’m feeling low today.")
    nudge = generate_reflective_nudge(user_id, tier, message)

    return {
        "statusCode": 200,
        "body": json.dumps({
            "user_id": user_id,
            "tier": tier,
            "message": message,
            "nudge": nudge
        }),
    }
