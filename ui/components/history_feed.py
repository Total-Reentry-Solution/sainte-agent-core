import streamlit as st
import pandas as pd
import requests

def render_history_feed(API_BASE):
    st.markdown("<h3 style='color:#00FFA3;'>Check-In History</h3>", unsafe_allow_html=True)
    try:
        r = requests.get(f"{API_BASE}/checkins")
        if r.status_code != 200:
            st.error("Failed to retrieve history.")
            return

        data = r.json()
        if not data:
            st.info("No check-ins available yet.")
            return

        # Safe conversion to DataFrame
        df = pd.DataFrame(data)
        if "tier" not in df.columns:
            df["tier"] = "Unknown"
        if "timestamp" not in df.columns:
            df["timestamp"] = None

        tier_icons = {"Stable":"🟢 Stable","At-Risk":"🟡 At-Risk","Critical":"🔴 Critical","Auto":"⚪ Auto","Unknown":"⚫ Unknown"}
        df["Tier"] = df["tier"].map(tier_icons).fillna("⚫ Unknown")
        df = df.sort_values("timestamp", ascending=False)

        st.dataframe(df[["timestamp","user_id","Tier","message","response"]], use_container_width=True)

    except Exception as e:
        st.error(f"Error fetching data: {e}")
