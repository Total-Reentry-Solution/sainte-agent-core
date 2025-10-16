# ui/components/history_feed.py
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
    st.markdown("<h3 style='color:#00FFA3;'>Check-In History</h3>", unsafe_allow_html=True)

    # Auto-refresh every 30 seconds for EventBridge updates
    st_autorefresh(interval=30 * 1000, key="refresh_history")

    with st.expander("Filters & Options", expanded=True):
        col_src, col_user, col_tier = st.columns([1, 1, 2])

        # ---- Data Source ----
        with col_src:
            source = st.radio(
                "Data Source",
                ["API Gateway", "Direct AWS (DynamoDB)"],
                help="Direct AWS requires valid local AWS credentials (boto3).",
            )

        # ---- Fetch Data ----
        if source == "API Gateway":
            df = _safe_fetch(lambda: fetch_checkins_via_api(API_BASE))
        else:
            df = _safe_fetch(lambda: fetch_checkins_via_dynamodb())

        # ---- Handle Empty ----
        if df is None or df.empty:
            st.info("No check-ins available yet.")
            return

        # ---- Filter Controls ----
        users = sorted([u for u in df["user_id"].dropna().unique().tolist() if u])
        with col_user:
            user_filter = st.multiselect("Users", options=users, default=[])

        with col_tier:
            tier_options = list(TIER_LABELS.keys())
            tier_filter = st.multiselect("Tiers", options=tier_options, default=tier_options)

        col_date, col_search, col_auto = st.columns([1.2, 1.2, 1])
        with col_date:
            # Default: last 30 days
            default_start = (datetime.now(timezone.utc) - timedelta(days=30)).date()
            default_end = datetime.now(timezone.utc).date()
            date_range = st.date_input(
                "Date Range",
                value=(default_start, default_end),
                help="Filter by timestamp (UTC).",
            )

        with col_search:
            query = st.text_input("Search message or response")

        with col_auto:
            include_auto = st.toggle("Include Auto Nudges", value=True)

        # ---- Apply Filters ----
        view = _apply_filters(df, user_filter, tier_filter, include_auto, date_range, query)

    # ---- KPI Section ----
    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.metric("Total Check-ins", f"{len(view):,}")
    with k2:
        st.metric("Unique Users", f"{view['user_id'].nunique():,}")
    with k3:
        st.metric("Auto Nudges", f"{(view['tier'] == 'Auto').sum():,}")
    with k4:
        last_ts = (
            view["timestamp"].max().strftime("%Y-%m-%d %H:%M UTC")
            if not view["timestamp"].isna().all()
            else "—"
        )
        st.metric("Last Activity", last_ts)

    # ---- Format for Display ----
    view["Tier"] = view["tier"].map(TIER_LABELS).fillna("⚫ Unknown")
    view["Time (UTC)"] = view["timestamp"].dt.strftime("%Y-%m-%d %H:%M")
    view = view.sort_values("timestamp", ascending=False)

    show_cols = ["Time (UTC)", "user_id", "Tier", "message", "response"]
    show_cols = [c for c in show_cols if c in view.columns]

    st.dataframe(view[show_cols], use_container_width=True, hide_index=True)

    # ---- Export ----
    csv = view.drop(columns=["embedding"], errors="ignore").to_csv(index=False)
    st.download_button(
        label="⬇️ Download Filtered CSV",
        data=csv,
        file_name="sainte_checkins_filtered.csv",
        mime="text/csv",
        type="primary",
    )


def _safe_fetch(fetch_fn):
    """Wrapper for safe API/Dynamo fetch."""
    try:
        df = fetch_fn()
        return df
    except Exception as e:
        st.error(f"Failed to load data: {e}")
        return None


def _apply_filters(df, user_filter, tier_filter, include_auto, date_range, query):
    """Apply filtering logic for the dashboard."""
    view = df.copy()

    # --- Date filter ---
    if isinstance(date_range, (list, tuple)) and len(date_range) == 2:
        start_dt = datetime.combine(date_range[0], datetime.min.time(), tzinfo=timezone.utc)
        end_dt = datetime.combine(date_range[1], datetime.max.time(), tzinfo=timezone.utc)
        view = view[(view["timestamp"] >= start_dt) & (view["timestamp"] <= end_dt)]

    # --- User filter ---
    if user_filter:
        view = view[view["user_id"].isin(user_filter)]

    # --- Tier filter ---
    if tier_filter:
        view = view[view["tier"].isin(tier_filter)]

    # --- Auto toggle ---
    if not include_auto:
        view = view[~(view["tier"] == "Auto")]

    # --- Search query ---
    if query.strip():
        q = query.lower().strip()
        view = view[
            view["message"].astype(str).str.lower().str.contains(q, na=False)
            | view["response"].astype(str).str.lower().str.contains(q, na=False)
        ]

    return view
