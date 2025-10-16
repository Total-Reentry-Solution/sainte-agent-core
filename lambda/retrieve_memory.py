import boto3
import json
import os
import math
from decimal import Decimal
from boto3.dynamodb.conditions import Key

# ===== AWS CONFIGURATION =====
REGION = os.getenv("AWS_REGION", "us-east-2")
bedrock = boto3.client("bedrock-runtime", region_name=REGION)
dynamodb = boto3.resource("dynamodb", region_name=REGION)
VECTORS_TABLE = os.getenv("VECTOR_TABLE", "SainiVectors")
vectors_table = dynamodb.Table(VECTORS_TABLE)


# ===== Titan v2 EMBEDDING =====
def get_embedding(text: str):
    """Generate Titan v2 embedding (correct schema for us-east-2)."""
    payload = {"inputText": text}

    response = bedrock.invoke_model(
        modelId="amazon.titan-embed-text-v2:0",
        body=json.dumps(payload),
        contentType="application/json",
        accept="application/json"
    )
    result = json.loads(response["body"].read())

    # Titan sometimes returns either “embeddings” or “embedding”
    if "embeddings" in result and isinstance(result["embeddings"], list):
        return result["embeddings"][0]
    elif "embedding" in result:
        return result["embedding"]
    else:
        raise ValueError(f"Unexpected Titan response format: {json.dumps(result)[:300]}")


# ===== COSINE SIMILARITY =====
def cosine_similarity(vec1, vec2):
    """Compute cosine similarity between two numeric vectors."""
    dot = sum(a * b for a, b in zip(vec1, vec2))
    norm1 = math.sqrt(sum(a * a for a in vec1))
    norm2 = math.sqrt(sum(b * b for b in vec2))
    if norm1 == 0 or norm2 == 0:
        return 0.0
    return dot / (norm1 * norm2 + 1e-9)


# ===== MAIN LAMBDA HANDLER =====
def lambda_handler(event, context):
    """Retrieve top-K most semantically related memories for a given user query."""
    try:
        # Parse event safely
        if "body" in event and isinstance(event["body"], str):
            body = json.loads(event["body"])
        else:
            body = event

        user_id = body.get("user_id")
        query_text = body.get("query", "").strip()
        top_k = int(body.get("top_k", 3))

        if not user_id or not query_text:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "Missing user_id or query"})
            }

        print(f"[RetrieveMemory] User={user_id}, Query='{query_text}', TopK={top_k}")

        # --- 1️⃣ Generate query embedding ---
        query_embedding = get_embedding(query_text)
        print(f"[Titan] Query embedding length: {len(query_embedding)}")

        # --- 2️⃣ Retrieve user’s memory items ---
        resp = vectors_table.scan()
        items = [item for item in resp.get("Items", []) if item.get("user_id") == user_id]

        if not items:
            print(f"[RetrieveMemory] No records found for user {user_id}")
            return {
                "statusCode": 404,
                "body": json.dumps({"message": "No memories found for this user."})
            }

        # --- 3️⃣ Compute cosine similarity ---
        results = []
        for item in items:
            emb = [float(x) for x in item.get("embedding", [])]
            sim = cosine_similarity(query_embedding, emb)
            results.append({
                "vector_id": item.get("vector_id"),
                "timestamp": item.get("timestamp"),
                "message": item.get("message"),
                "response": item.get("response"),
                "tier": item.get("tier"),
                "similarity": round(sim, 4)
            })

        # --- 4️⃣ Sort & select top-K ---
        results.sort(key=lambda x: x["similarity"], reverse=True)
        top_items = results[:top_k]

        # --- 5️⃣ Return formatted response ---
        return {
            "statusCode": 200,
            "body": json.dumps({
                "user_id": user_id,
                "query": query_text,
                "top_k": top_k,
                "related_memories": top_items
            }, indent=2)
        }

    except Exception as e:
        print(f"❌ Error in retrieve_memory: {e}")
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }
