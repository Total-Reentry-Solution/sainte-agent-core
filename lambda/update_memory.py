# This Lambda takes every message from your /checkin flow, converts it into an embedding (semantic vector), and stores it in SainiVectors.

import boto3, json, os, uuid
from datetime import datetime

# Initialize clients
bedrock = boto3.client("bedrock-runtime", region_name="us-east-2")
dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(os.environ.get("TABLE_NAME", "SainiCheckins"))

# Optional: separate vector store table
VECTOR_TABLE = os.environ.get("VECTOR_TABLE", "SainiVectors")
vector_table = dynamodb.Table(VECTOR_TABLE)

def get_embedding(text):
    """Use Bedrock Titan Embeddings to convert text into vector"""
    response = bedrock.invoke_model(
        modelId="amazon.titan-embed-text-v1",
        body=json.dumps({"inputText": text}),
        contentType="application/json"
    )
    embedding = json.loads(response["body"].read())["embedding"]
    return embedding

def lambda_handler(event, context):
    body = json.loads(event.get("body", "{}"))
    user_id = body.get("user_id")
    message = body.get("message")
    tier = body.get("tier", "Unknown")
    response_text = body.get("response", "")

    # 1️⃣ Combine text for embedding
    combined_text = f"User:{user_id} | Msg:{message} | Tier:{tier} | Resp:{response_text}"
    embedding = get_embedding(combined_text)

    # 2️⃣ Save vector entry
    vector_table.put_item(
        Item={
            "vector_id": str(uuid.uuid4()),
            "user_id": user_id,
            "timestamp": datetime.utcnow().isoformat(),
            "embedding": embedding,
            "message": message,
            "tier": tier,
            "response": response_text
        }
    )

    return {
        "statusCode": 200,
        "body": json.dumps({"message": "Vector stored successfully."})
    }
