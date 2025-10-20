import os
import json
import requests
import pandas as pd
import streamlit as st


# ==========================================
# 🚀 API FETCH UTILITIES (with caching + normalization)
# ==========================================

@st.cache_data(ttl=60, show_spinner=False)
def fetch_checkins_via_api(api_base: str) -> pd.DataFrame:
    """
    Fetch check-in data via API Gateway endpoint and normalize.
    Works whether API Gateway returns a plain list or
    a wrapped {"statusCode":200,"body":"[...]"} shape.
    """
    try:
        url = f"{api_base}/checkins".rstrip("/")
        r = requests.get(url, timeout=20)
        r.raise_for_status()
        data = _unwrap_api_response(r)
        df = pd.DataFrame(data)
        return normalize_df(df)
    except Exception as e:
        st.error(f"❌ Failed to fetch via API: {e}")
        return pd.DataFrame()


@st.cache_data(ttl=60, show_spinner=False)
def fetch_user_analytics(api_base: str, user_id: str) -> dict:
    """
    Fetch analytics summary for a given user from /analytics endpoint.
    Returns a dictionary or {} if unavailable.
    """
    try:
        url = f"{api_base}/analytics"
        r = requests.get(url, params={"user_id": user_id}, timeout=10)
        r.raise_for_status()
        data = _unwrap_api_response(r)
        if isinstance(data, dict):
            return data
        if isinstance(data, list) and data:
            return data[0]
        return {}
    except Exception as e:
        st.warning(f"⚠️ Analytics unavailable for {user_id}: {e}")
        return {}


# ==========================================
# 🧩 UNIVERSAL API RESPONSE UNWRAPPER
# ==========================================
def _unwrap_api_response(resp):
    """
    Normalizes API Gateway responses.
    Handles shapes:
      • list of dicts
      • {"body": "[...json...]"}
      • {"statusCode": 200, "body": "[...json...]"}
    """
    try:
        data = resp.json()
    except Exception:
        return []

    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        body = data.get("body")
        if isinstance(body, list):
            return body
        if isinstance(body, str):
            try:
                return json.loads(body)
            except Exception:
                return []
        return data if "timestamp" in data else []
    return []


# ==========================================
# 🧭 NORMALIZATION
# ==========================================
def normalize_df(df: pd.DataFrame) -> pd.DataFrame:
    """Ensure consistent schema + datatypes for all UI components."""
    if df.empty:
        return df

    required_cols = {
        "timestamp": None,
        "user_id": "unknown",
        "tier": "Unknown",
        "message": "",
        "response": "",
        "tone": "neutral",
        "source": "N/A",
        "is_auto": False,
    }

    for col, default in required_cols.items():
        if col not in df.columns:
            df[col] = default

    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce", utc=True)

    for col in ["user_id", "tier", "message", "response", "tone", "source"]:
        df[col] = df[col].astype(str).fillna("")

    df["tier"] = df["tier"].str.strip().str.title()
    df["tone"] = df["tone"].str.strip().str.lower()

    return df.sort_values("timestamp", ascending=False).reset_index(drop=True)


# ==========================================
# 🧠 DIRECT DYNAMODB FETCH (when running locally)
# ==========================================
@st.cache_data(ttl=60, show_spinner=False)
def fetch_checkins_via_dynamodb(table_name: str = None, region: str = None) -> pd.DataFrame:
    """
    Optional direct DynamoDB read (requires AWS credentials).
    Used for debugging or running locally without API Gateway.
    """
    try:
        import boto3

        table_name = table_name or os.getenv("TABLE_NAME", "SainiCheckins")
        region = region or os.getenv("AWS_REGION", "us-east-2")

        dyn = boto3.resource("dynamodb", region_name=region)
        table = dyn.Table(table_name)

        items = []
        resp = table.scan()
        items.extend(resp.get("Items", []))
        while resp.get("LastEvaluatedKey"):
            resp = table.scan(ExclusiveStartKey=resp["LastEvaluatedKey"])
            items.extend(resp.get("Items", []))

        return normalize_df(pd.DataFrame(items))

    except Exception as e:
        st.error(f"⚠️ Failed to fetch from DynamoDB: {e}")
        return pd.DataFrame()


# ==========================================
# 👥 FETCH USER LIST (for dropdown)
# ==========================================
@st.cache_data(ttl=60, show_spinner=False)
def fetch_user_list(api_base: str):
    """
    Fetch unique user IDs from the /users endpoint.
    Returns a sorted list of strings.
    Works for API Gateway shapes:
      • ["user1","user2"]
      • {"body":"[\"user1\",\"user2\"]"}
      • {"statusCode":200,"body":"[\"user1\",\"user2\"]"}
    """
    try:
        url = f"{api_base}/users".rstrip("/")
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        data = _unwrap_api_response(r)

        # Normalize shape
        if isinstance(data, dict):
            data = data.get("users", [])
        if not isinstance(data, list):
            return []

        users = sorted([str(u) for u in data if u])
        return users

    except Exception as e:
        st.warning(f"⚠️ Could not load user list: {e}")
        return []
