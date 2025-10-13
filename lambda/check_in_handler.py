#Entry Lambda that receives user text → stores → classifies → gets Bedrock reply.

import json
import os 
import boto3
from datetime import datetime
from classify_state import classify_user_state
from respond_nudge import generate_nudge

dynamodb = boto3.resource("dynamodb")
TABLE_NAME = os.environ.get("TABLE_NAME", "SainiCheckins")

def lambda_handler(event, context):
    body = json.loads(event.get("body", "{}"))
    user_id = body.get("user_id")
    message = body.get("message")
    
    if not user_id and not message:
        return {"statusCode": 400 , "body": json.dumps({"error":"Missing user_id or message"})}
    
    # Classify State
    tier = classify_user_state(message)
    
    # Generate Response
    reply = generate_nudge(tier, message)
    
    table = dynamodb.Table(TABLE_NAME)
    table.put_item(
        Item={
            "user_id":user_id,
            "timestamp":datetime.utcnow().isoformat(),
            "message":message,
            "tier":tier,
            "response":reply
        }
    )
    
    return {
        "statusCode": 200,
        "body":json.dumps({"tier":tier, "response":reply})
    }
    
    