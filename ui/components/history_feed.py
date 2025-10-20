import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, timezone
from streamlit_autorefresh import st_autorefresh
from utils.api import fetch_checkins_via_api, fetch_checkins_via_dynamodb

TIER_LABELS = {
    "Stable": "🟢 Stable",
    "At-Risk": "🟡 At-Risk",
    "Critical": "🔴 Critical",
    "Auto": "⚪ Auto",
    "Unknown": "⚫ Unknown",
}

def render_history_feed(API_BASE: str):
    st.markdown("<h3 style='color:#00FFA3;'>📜 Check-In History</h3>", unsafe_allow_html=True)
    st.caption("Your emotional journey — visualized through time.")
    st_autorefresh(interval=30 * 1000, key="refresh_history")

    with st.container():
        col_src, col_user, col_tier = st.columns([1.2, 1, 2])

        with col_src:
            source = st.radio(
                "Data Source", ["API Gateway", "Direct AWS (DynamoDB)"],
                help="Direct AWS requires configured AWS credentials."
            )

        if source == "API Gateway":
            df = _safe_fetch(lambda: fetch_checkins_via_api(API_BASE))
        else:
            df = _safe_fetch(lambda: fetch_checkins_via_dynamodb())

        if df is None or df.empty:
            st.info("No emotional check-ins yet — your first reflection will appear here 🌱.")
            return

        # --- Filtering controls ---
        users = sorted(df["user_id"].dropna().unique().tolist())
        with col_user:
            user_filter = st.multiselect("User", options=users, placeholder="Select users")

        with col_tier:
            tier_filter = st.multiselect("Tiers", options=TIER_LABELS.keys(), default=list(TIER_LABELS.keys()))

        col_date, col_search, col_auto = st.columns([1.3, 1.2, 0.8])
        with col_date:
            start = (datetime.now(timezone.utc) - timedelta(days=30)).date()
            end = datetime.now(timezone.utc).date()
            date_range = st.date_input("Date Range", value=(start, end))

        with col_search:
            query = st.text_input("Search reflections or messages")

        with col_auto:
            include_auto = st.toggle("Include Auto Nudges", value=True)

        view = _apply_filters(df, user_filter, tier_filter, include_auto, date_range, query)

        # --- KPIs ---
        st.markdown("<hr style='border-color:#222;'>", unsafe_allow_html=True)
        k1, k2, k3, k4 = st.columns(4)
        with k1: st.metric("Total Reflections", f"{len(view):,}")
        with k2: st.metric("Unique Users", f"{view['user_id'].nunique():,}")
        with k3: st.metric("Auto Nudges", f"{(view['tier'] == 'Auto').sum():,}")
        with k4:
            last_ts = (
                view["timestamp"].max().strftime("%Y-%m-%d %H:%M UTC")
                if not view["timestamp"].isna().all()
                else "—"
            )
            st.metric("Last Activity", last_ts)

        # --- Data Table ---
        view["Tier"] = view["tier"].map(TIER_LABELS).fillna("⚫ Unknown")
        view["Time (UTC)"] = view["timestamp"].dt.strftime("%Y-%m-%d %H:%M")
        view = view.sort_values("timestamp", ascending=False)
        cols = ["Time (UTC)", "user_id", "Tier", "message", "response"]
        st.dataframe(view[cols], use_container_width=True, hide_index=True)

        # --- Export Option ---
        csv = view.drop(columns=["embedding"], errors="ignore").to_csv(index=False)
        st.download_button(
            "⬇️ Download Reflections CSV", csv, "sainte_reflections.csv", "text/csv"
        )

def _safe_fetch(fetch_fn):
    try:
        return fetch_fn()
    except Exception as e:
        st.error(f"Failed to fetch data: {e}")
        return None

def _apply_filters(df, user_filter, tier_filter, include_auto, date_range, query):
    view = df.copy()
    if len(date_range) == 2:
        start_dt = datetime.combine(date_range[0], datetime.min.time(), tzinfo=timezone.utc)
        end_dt = datetime.combine(date_range[1], datetime.max.time(), tzinfo=timezone.utc)
        view = view[(view["timestamp"] >= start_dt) & (view["timestamp"] <= end_dt)]
    if user_filter:
        view = view[view["user_id"].isin(user_filter)]
    if tier_filter:
        view = view[view["tier"].isin(tier_filter)]
    if not include_auto:
        view = view[~(view["tier"] == "Auto")]
    if query.strip():
        q = query.lower()
        view = view[
            view["message"].astype(str).str.lower().str.contains(q, na=False)
            | view["response"].astype(str).str.lower().str.contains(q, na=False)
        ]
    return view
