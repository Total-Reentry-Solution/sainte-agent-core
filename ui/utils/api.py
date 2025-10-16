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
    """Fetch check-in data via API Gateway endpoint."""
    try:
        url = f"{api_base}/checkins".rstrip("/")
        r = requests.get(url, timeout=20)
        r.raise_for_status()
        data = r.json() or []
        df = pd.DataFrame(data)
        return normalize_df(df)
    except Exception as e:
        st.error(f"❌ Failed to fetch via API: {e}")
        return pd.DataFrame()


# ==========================================
# 🧭 NORMALIZATION
# ==========================================

def normalize_df(df: pd.DataFrame) -> pd.DataFrame:
    """Ensure consistent schema + datatypes for all UI components."""
    if df.empty:
        return df

    # --- Ensure required columns exist ---
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

    # --- Parse timestamps safely ---
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce", utc=True)

    # --- Clean string columns ---
    for col in ["user_id", "tier", "message", "response", "tone", "source"]:
        df[col] = df[col].astype(str).fillna("")

    # --- Normalize capitalization for tier/tone ---
    df["tier"] = df["tier"].str.strip().str.title()
    df["tone"] = df["tone"].str.strip().str.lower()

    # --- Sort by most recent first ---
    df = df.sort_values("timestamp", ascending=False).reset_index(drop=True)

    return df


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

        df = pd.DataFrame(items)
        return normalize_df(df)

    except Exception as e:
        st.error(f"⚠️ Failed to fetch from DynamoDB: {e}")
        return pd.DataFrame()
