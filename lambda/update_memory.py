import boto3
import json
import os
import uuid
from datetime import datetime
from decimal import Decimal

# ===== AWS CONFIGURATION =====
REGION = os.getenv("AWS_REGION", "us-east-2")
bedrock = boto3.client("bedrock-runtime", region_name=REGION)
dynamodb = boto3.resource("dynamodb", region_name=REGION)

# ===== TABLE REFERENCES =====
CHECKINS_TABLE = os.getenv("TABLE_NAME", "SainiCheckins")
VECTORS_TABLE = os.getenv("VECTOR_TABLE", "SainiVectors")

checkins_table = dynamodb.Table(CHECKINS_TABLE)
vectors_table = dynamodb.Table(VECTORS_TABLE)


# ===== UTIL: FLOAT → DECIMAL =====
def float_to_decimal(obj):
    """Recursively convert all floats to Decimal for DynamoDB."""
    if isinstance(obj, list):
        return [float_to_decimal(i) for i in obj]
    elif isinstance(obj, dict):
        return {k: float_to_decimal(v) for k, v in obj.items()}
    elif isinstance(obj, float):
        return Decimal(str(obj))
    else:
        return obj


# ===== EMBEDDING GENERATOR =====
def get_embedding(text: str):
    """
    Generate text embedding using Amazon Titan v2 (Bedrock, us-east-2).
    Payload schema must be minimal: {"inputText": "..."}.
    """
    try:
        payload = {"inputText": text}

        response = bedrock.invoke_model(
            modelId="amazon.titan-embed-text-v2:0",
            body=json.dumps(payload),
            contentType="application/json",
            accept="application/json"
        )

        result = json.loads(response["body"].read())

        # Titan v2 always returns: {"embedding": [float, float, ...]}
        if "embedding" in result:
            return result["embedding"]
        else:
            raise KeyError(f"Unexpected Titan response format: {result}")

    except Exception as e:
        print(f"❌ Titan embedding generation failed: {e}")
        raise


# ===== MAIN LAMBDA HANDLER =====
def lambda_handler(event, context):
    """
    Triggered asynchronously from check_in_handler to persist semantic memory.
    Stores [user_id, timestamp, message, tier, response, embedding] in SainiVectors.
    """
    try:
        # Handle both API Gateway & direct Lambda invokes
        if "body" in event and isinstance(event["body"], str):
            body = json.loads(event["body"])
        else:
            body = event

        user_id = body.get("user_id")
        message = body.get("message", "").strip()
        tier = body.get("tier", "Unknown")
        response_text = body.get("response", "").strip()

        if not user_id or not message:
            print("⚠️ Missing user_id or message.")
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "Missing user_id or message"})
            }

        # Combine text context for embedding
        combined_text = (
            f"User: {user_id} | Tier: {tier} | "
            f"Message: {message} | Response: {response_text}"
        )

        # Generate Titan embedding
        embedding = get_embedding(combined_text)
        print(f"[Titan] Embedding length: {len(embedding)}")

        # Convert floats → Decimal for DynamoDB
        embedding_decimal = float_to_decimal(embedding)

        # Write record to DynamoDB
        record_id = str(uuid.uuid4())
        vectors_table.put_item(
            Item={
                "vector_id": record_id,
                "user_id": user_id,
                "timestamp": datetime.utcnow().isoformat(),
                "message": message,
                "tier": tier,
                "response": response_text,
                "embedding": embedding_decimal,
            }
        )

        print(f"✅ Vector memory stored successfully for user {user_id} (ID={record_id})")
        return {
            "statusCode": 200,
            "body": json.dumps({
                "message": "Vector stored successfully",
                "vector_id": record_id,
                "embedding_dim": len(embedding)
            }),
        }

    except Exception as e:
        print(f"❌ Error in update_memory: {e}")
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)}),
        }
