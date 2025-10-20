import boto3, json, os
from datetime import datetime
from collections import Counter

REGION = "us-east-2"
TABLE_NAME = os.getenv("TABLE_NAME", "SainiCheckins")
dynamodb = boto3.resource("dynamodb", region_name=REGION)
table = dynamodb.Table(TABLE_NAME)

def lambda_handler(event, context):
    print("📩 Incoming:", json.dumps(event))
    path = event.get("path", "")
    method = event.get("httpMethod", "")
    params = event.get("queryStringParameters") or {}
    body = json.loads(event.get("body", "{}")) if event.get("body") else {}

    if path == "/users" and method == "GET":
        return json_response(200, get_users())

    if path == "/checkins" and method == "GET":
        return json_response(200, get_checkins(params.get("user_id")))

    if path == "/checkin" and method == "POST":
        return json_response(200, post_checkin(body))

    if path == "/analytics" and method == "GET":
        uid = params.get("user_id")
        return json_response(200, compute_user_analytics(uid))

    return json_response(404, {"error": f"Route not found: {path} {method}"})


# === HELPERS ===
def get_users():
    users = set()
    scan = {"ProjectionExpression": "user_id"}
    while True:
        resp = table.scan(**scan)
        for i in resp.get("Items", []):
            if "user_id" in i:
                users.add(i["user_id"])
        if "LastEvaluatedKey" not in resp:
            break
        scan["ExclusiveStartKey"] = resp["LastEvaluatedKey"]
    return sorted(users)

def get_checkins(user_id=None):
    items, scan = [], {}
    while True:
        resp = table.scan(**scan)
        items.extend(resp.get("Items", []))
        if "LastEvaluatedKey" not in resp:
            break
        scan["ExclusiveStartKey"] = resp["LastEvaluatedKey"]

    if user_id:
        items = [i for i in items if i.get("user_id") == user_id]
    for i in items:
        if "timestamp" in i:
            try:
                i["timestamp"] = i["timestamp"].split(".")[0]
            except Exception:
                pass
    return sorted(items, key=lambda x: x.get("timestamp", ""), reverse=True)

def post_checkin(body):
    user_id = body.get("user_id", "guest_user")
    message = body.get("message", "")
    tier = body.get("tier", "Auto")
    tone = body.get("tone", "gentle")
    reflection = body.get("response", "Noted.")
    if not message:
        return {"error": "Missing message."}

    item = {
        "user_id": user_id,
        "timestamp": datetime.utcnow().isoformat(),
        "message": message,
        "tier": tier,
        "tone": tone,
        "response": reflection,
        "source": "Sainte-CheckIn"
    }
    table.put_item(Item=item)
    return {"status": "ok", "user_id": user_id}


# === ANALYTICS ===
def compute_user_analytics(user_id=None):
    data = get_checkins(user_id)
    if not data:
        return {"user_id": user_id, "error": "No data"}

    tiers = [d.get("tier", "Unknown") for d in data]
    tones = [d.get("tone", "Unknown") for d in data]
    tier_counts = Counter(tiers)
    tone_counts = Counter(tones)
    return {
        "user_id": user_id,
        "total_reflections": len(data),
        "tier_distribution": dict(tier_counts),
        "tone_distribution": dict(tone_counts),
        "latest_tier": data[0].get("tier"),
        "latest_tone": data[0].get("tone"),
        "last_checkin": data[0].get("timestamp"),
    }

def json_response(status, data):
    return {
        "statusCode": status,
        "headers": {
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET,POST,OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type",
        },
        "body": json.dumps(data, ensure_ascii=False),
    }
