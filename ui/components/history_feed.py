import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, timezone
from streamlit_autorefresh import st_autorefresh
import requests
from utils.api import fetch_checkins_via_api, fetch_checkins_via_dynamodb, fetch_user_list

TIER_LABELS = {
    "Stable":  "🟢 Stable",
    "At-Risk": "🟡 At-Risk",
    "Critical":"🔴 Critical",
    "Auto":    "⚪ Auto",
    "Unknown": "⚫ Unknown",
}

def render_history_feed(API_BASE: str):
    st.markdown("<h3 style='color:#00FFA3;'>📜 Check-In History</h3>", unsafe_allow_html=True)
    st.caption("Your emotional journey — visualized through time.")
    st_autorefresh(interval=30_000, key="refresh_history")

    col_src, col_user, col_tier = st.columns([1.2, 1, 2])
    with col_src:
        source = st.radio("Data Source", ["API Gateway", "Direct AWS (DynamoDB)"], help="Direct AWS requires local AWS creds.")

    df = fetch_checkins_via_api(API_BASE) if source == "API Gateway" else fetch_checkins_via_dynamodb()
    if df is None or df.empty:
        st.info("No emotional check-ins yet — your first reflection will appear here 🌱.")
        return

    # --- controls
    users = fetch_user_list(API_BASE)
    with col_user:
        user_filter = st.multiselect("User", options=users, placeholder="Select users")
    with col_tier:
        tier_filter = st.multiselect("Tiers", options=list(TIER_LABELS.keys()), default=list(TIER_LABELS.keys()))

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
    if view.empty:
        st.warning("No results match the filters.")
        return

    _render_global_metrics(view)

    # user analytics
    if user_filter:
        _render_user_analytics(API_BASE, view, user_filter)

    # table
    view = view.sort_values("timestamp", ascending=False).copy()
    view["Tier"] = view["tier"].map(TIER_LABELS).fillna("⚫ Unknown")
    view["Time (UTC)"] = view["timestamp"].dt.strftime("%Y-%m-%d %H:%M")
    cols = ["Time (UTC)", "user_id", "Tier", "message", "response"]
    st.dataframe(view[cols], use_container_width=True, hide_index=True)

    # export
    csv = view.drop(columns=["embedding"], errors="ignore").to_csv(index=False)
    st.download_button("⬇️ Download Reflections CSV", csv, "sainte_reflections.csv", "text/csv")


# ---------- helpers ----------
def _apply_filters(df, users, tiers, include_auto, date_range, query):
    v = df.copy()
    if len(date_range) == 2:
        s = datetime.combine(date_range[0], datetime.min.time(), tzinfo=timezone.utc)
        e = datetime.combine(date_range[1], datetime.max.time(), tzinfo=timezone.utc)
        v = v[(v["timestamp"] >= s) & (v["timestamp"] <= e)]
    if users: v = v[v["user_id"].isin(users)]
    if tiers: v = v[v["tier"].isin(tiers)]
    if not include_auto: v = v[v["tier"] != "Auto"]
    if query.strip():
        q = query.lower()
        v = v[v["message"].str.lower().str.contains(q, na=False) | v["response"].str.lower().str.contains(q, na=False)]
    return v

def _render_global_metrics(view):
    st.markdown("<hr style='border-color:#222;'>", unsafe_allow_html=True)
    k1, k2, k3, k4, k5 = st.columns(5)
    with k1: st.metric("Total Reflections", f"{len(view):,}")
    with k2: st.metric("Unique Users", f"{view['user_id'].nunique():,}")
    with k3: st.metric("Auto Nudges", f"{(view['tier'] == 'Auto').sum():,}")
    with k4:
        tone = "—"
        if "tone" in view.columns and not view["tone"].isna().all():
            try: tone = view["tone"].mode()[0]
            except: pass
        st.metric("Most Common Tone", str(tone).capitalize())
    with k5:
        last_ts = "—"
        try:
            last_ts = view["timestamp"].max().strftime("%Y-%m-%d %H:%M UTC")
        except: pass
        st.metric("Last Activity", last_ts)

def _render_user_analytics(API_BASE, view, users):
    st.markdown("### 🧩 User Analytics")
    for uid in users:
        user_df = view[view["user_id"] == uid]
        if user_df.empty: continue

        st.markdown(f"<h5 style='color:#00FFA3;'>👤 {uid}</h5>", unsafe_allow_html=True)

        # Optional server-side summary (fast and lightweight)
        summary = {}
        try:
            r = requests.get(f"{API_BASE}/analytics", params={"user_id": uid}, timeout=8)
            if r.status_code == 200: summary = r.json()
        except: pass

        c1, c2, c3, c4 = st.columns(4)
        with c1: st.metric("Total Reflections", len(user_df))
        with c2: st.metric("Latest Tier", summary.get("latest_tier","—"))
        with c3: st.metric("Latest Tone", summary.get("latest_tone","—"))
        with c4: st.metric("Last Check-in", summary.get("last_checkin","—"))

        # Charts
        st.caption("Tier distribution")
        st.bar_chart(user_df["tier"].value_counts())

        if "tone" in user_df.columns and not user_df["tone"].isna().all():
            st.caption("Tone distribution")
            st.bar_chart(user_df["tone"].value_counts())

        st.caption("Reflection frequency (daily)")
        by_day = user_df.groupby(user_df["timestamp"].dt.date)["user_id"].count()
        st.line_chart(by_day)
