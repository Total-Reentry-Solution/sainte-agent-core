# Entry Lambda that receives user text → classifies → retrieves context → gets Bedrock reply → stores result.

import json
import os
import boto3
from datetime import datetime
from classify_state import classify_user_state
from respond_nudge import generate_reflective_nudge as generate_nudge

# ===== AWS CLIENTS =====
REGION = os.getenv("AWS_REGION", "us-east-2")
dynamodb = boto3.resource("dynamodb", region_name=REGION)
lambda_client = boto3.client("lambda", region_name=REGION)
TABLE_NAME = os.getenv("TABLE_NAME", "SainiCheckins")
table = dynamodb.Table(TABLE_NAME)


def lambda_handler(event, context):
    try:
        # --- Parse incoming event ---
        if "body" in event and isinstance(event["body"], str):
            body = json.loads(event["body"])
        else:
            body = event  # direct invoke (console or internal call)

        user_id = body.get("user_id")
        message = body.get("message")

        if not user_id or not message:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "Missing user_id or message"})
            }

        # --- Step 1️⃣: Classify emotion tier ---
        tier = classify_user_state(message)

        # --- Step 2️⃣: Retrieve memory context (top-3 past related) ---
        related_memories = []
        try:
            mem_response = lambda_client.invoke(
                FunctionName="retrieve_memory",
                InvocationType="RequestResponse",
                Payload=json.dumps({
                    "user_id": user_id,
                    "query": message,
                    "top_k": 3
                })
            )
            mem_payload = json.loads(mem_response["Payload"].read().decode("utf-8"))
            related_memories = json.loads(mem_payload.get("body", "{}")).get("related_memories", [])
        except Exception as mem_err:
            print(f"⚠️ Memory retrieval failed: {mem_err}")

        # --- Step 3️⃣: Build context summary for Bedrock nudge ---
        context_snippet = "\n".join(
            [f"- {m['message']} (Response: {m['response']})" for m in related_memories]
        ) or "No prior relevant memories found."

        # --- Step 4️⃣: Generate reflective nudge ---
        prompt_context = (
            f"User message: {message}\n"
            f"Emotional tier: {tier}\n"
            f"Past related experiences:\n{context_snippet}\n\n"
            "Generate one short, trauma-informed reflective response that feels empathetic, "
            "gentle, and connected to user’s past experiences if relevant."
        )

        reply = generate_nudge(user_id, tier, prompt_context)

        # --- Step 5️⃣: Store to SainiCheckins table ---
        table.put_item(Item={
            "user_id": user_id,
            "timestamp": datetime.utcnow().isoformat(),
            "message": message,
            "tier": tier,
            "response": reply
        })

        # --- Step 6️⃣: Trigger async update_memory Lambda ---
        try:
            lambda_client.invoke(
                FunctionName="update_memory",
                InvocationType="Event",
                Payload=json.dumps({
                    "user_id": user_id,
                    "message": message,
                    "tier": tier,
                    "response": reply
                })
            )
        except Exception as e:
            print(f"⚠️ update_memory trigger failed: {e}")

        # --- Step 7️⃣: Return composite response ---
        return {
            "statusCode": 200,
            "body": json.dumps({
                "user_id": user_id,
                "tier": tier,
                "response": reply,
                "related_memories": related_memories
            })
        }

    except Exception as e:
        print(f"❌ Error in check_in_handler: {e}")
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }
