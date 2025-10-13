# Generates a gentle Bedrock-based or local fallback reply.
import os 
import boto3

import os
import boto3

def generate_nudge(tier: str, message: str) -> str:
    """Create tier-based reply via Bedrock (or fallback text)."""
    try:
        bedrock = boto3.client("bedrock-runtime", region_name=os.getenv("AWS_REGION", "us-east-1"))
        prompt = f"User emotional tier: {tier}. Message: {message}. Respond with a brief trauma-informed supportive nudge."
        response = bedrock.invoke_model(
            modelId="anthropic.claude-3-sonnet-20240229-v1:0",
            body=prompt.encode("utf-8"),
            accept="application/json",
            contentType="text/plain"
        )
        return response["body"].read().decode("utf-8")
    except Exception:
        # fallback deterministic replies
        fallbacks = {
            "Stable": "You’re doing steady work—want to stay in this rhythm or stretch a bit today?",
            "Stirred": "Seems like something’s shifting—want to talk about it or take a breather?",
            "At-Risk": "I noticed some strain—would it help to look at next steps or just pause?",
            "Critical": "This sounds heavy. I can stay here, or bring in someone you trust.",
        }
        return fallbacks.get(tier, "I’m here with you.")
