import os
import json
import boto3
import random
import math

# ===== AWS CONFIGURATION =====
REGION = os.getenv("AWS_REGION", "us-east-2")
bedrock = boto3.client("bedrock-runtime", region_name=REGION)

# ===== TITAN EMBEDDING MODEL (AVAILABLE IN us-east-2) =====
EMBED_MODEL = "amazon.titan-embed-text-v2:0"


# ===== UTILITIES =====
def get_embedding(text: str):
    """Generate Titan embedding for the given text (us-east-2, v2 schema)."""
    payload = {
        "inputText": text
    }

    response = bedrock.invoke_model(
        modelId="amazon.titan-embed-text-v2:0",
        body=json.dumps(payload),
        contentType="application/json",
        accept="application/json"
    )

    result = json.loads(response["body"].read())
    return result["embedding"]
    


def similarity_score(vec):
    """Compute a small numeric summary to modulate tone."""
    magnitude = math.sqrt(sum(v**2 for v in vec))
    scaled = (magnitude % 1)  # normalize fractional
    return round(scaled, 2)


def generate_reflective_nudge(user_id: str, tier: str, message: str) -> str:
    """Generate a trauma-informed nudge using Titan embeddings instead of text model."""
    try:
        # Generate semantic vector of the user's message
        emb = get_embedding(message)
        sim = similarity_score(emb)
        print(f"[Titan] Embedding magnitude ratio: {sim}")

        # Map similarity to tone shift
        if sim < 0.3:
            tone = "gentle grounding"
        elif sim < 0.6:
            tone = "balanced encouragement"
        else:
            tone = "energizing reassurance"

        base_prompts = {
            "Stable": [
                f"You’re holding steady—stay with that {tone} today.",
                f"Keep your rhythm; your {tone} presence matters.",
            ],
            "Stirred": [
                f"Something’s moving inside—meet it with {tone}.",
                f"You’re noticing the shift; respond with {tone} care.",
            ],
            "At-Risk": [
                f"You’ve faced harder moments; find {tone} within reach.",
                f"It’s okay to slow down—let {tone} guide your next step.",
            ],
            "Critical": [
                f"This moment feels heavy—let {tone} be your anchor.",
                f"You’re not alone; reach out or just breathe with {tone}.",
            ],
        }

        # Randomly pick one reflective nudge
        nudge = random.choice(base_prompts.get(tier, ["I’m here with you."]))
        return nudge

    except Exception as e:
        print(f"⚠️ Titan embedding nudge failed: {e}")
        fallbacks = {
            "Stable": "You’re doing steady work—want to stay in this rhythm or stretch a bit today?",
            "Stirred": "Seems like something’s shifting—want to talk about it or take a breather?",
            "At-Risk": "I noticed some strain—would it help to look at next steps or just pause?",
            "Critical": "This sounds heavy. I can stay here, or bring in someone you trust.",
        }
        return fallbacks.get(tier, "I’m here with you.")


# ===== LAMBDA HANDLER =====
def lambda_handler(event, context):
    """AWS Lambda entry point."""
    body = json.loads(event.get("body", "{}"))
    user_id = body.get("user_id", "user123")
    tier = body.get("tier", "At-Risk")
    message = body.get("message", "Feeling emotionally tired but hopeful.")

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
