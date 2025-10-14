# Generates a trauma-informed, context-aware reply using Amazon Bedrock or fallback text.

import os
import json
import boto3
from boto3.dynamodb.conditions import Key

# Initialize AWS clients
dynamodb = boto3.resource("dynamodb")
bedrock = boto3.client("bedrock-runtime", region_name=os.getenv("AWS_REGION", "us-east-2"))

# Environment variables
VECTOR_TABLE = os.getenv("VECTOR_TABLE", "SainiVectors")
vector_table = dynamodb.Table(VECTOR_TABLE)


def retrieve_recent_context(user_id: str, top_k: int = 3) -> str:
    """
    Fetches the most recent 'top_k' check-ins for a user to build short-term memory.
    Requires a GSI on user_id in SainiVectors.
    """
    try:
        response = vector_table.query(
            IndexName="user_id-index",  # ✅ must match the actual GSI name
            KeyConditionExpression=Key("user_id").eq(user_id),
            Limit=top_k,
            ScanIndexForward=False  # Newest first
        )
        items = response.get("Items", [])
        if not items:
            return ""

        context_snippets = [
            f"[{i['timestamp']}] {i['tier']}: {i['message']}"
            for i in items
        ]
        return "\n".join(context_snippets)
    except Exception as e:
        print(f"⚠️ Context retrieval failed: {e}")
        return ""


def generate_nudge(tier: str, message: str, user_id: str = None) -> str:
    """Create tier-based reply via Bedrock (or fallback text)."""
    # 1️⃣ Gather Context
    context = retrieve_recent_context(user_id, top_k=3) if user_id else ""

    # 2️⃣ Build Prompt with Context
    prompt = (
        f"Context from previous check-ins:\n{context}\n\n"
        f"Current user emotional tier: {tier}\n"
        f"Latest message: {message}\n\n"
        f"Respond briefly, in a trauma-informed and supportive tone. "
        f"Reference any relevant prior progress if appropriate."
    )

    # 3️⃣ Call Bedrock (Claude 3 Sonnet)
    try:
        response = bedrock.invoke_model(
            modelId="anthropic.claude-3-sonnet-20240229-v1:0",
            body=prompt.encode("utf-8"),
            accept="application/json",
            contentType="text/plain"
        )
        return response["body"].read().decode("utf-8")

    except Exception as e:
        print(f"⚠️ Bedrock call failed: {e}")

        # 4️⃣ Fallback deterministic replies
        fallbacks = {
            "Stable": "You’re doing steady work—want to stay in this rhythm or stretch a bit today?",
            "Stirred": "Seems like something’s shifting—want to talk about it or take a breather?",
            "At-Risk": "I noticed some strain—would it help to look at next steps or just pause?",
            "Critical": "This sounds heavy. I can stay here, or bring in someone you trust.",
        }
        return fallbacks.get(tier, "I’m here with you.")
