import streamlit as st
import requests, pandas as pd
import matplotlib.pyplot as plt

def render_emotion_chart(API_BASE):
    st.markdown("<h3 style='color:#00FFA3;'>📈 Emotional Trend</h3>", unsafe_allow_html=True)
    try:
        r = requests.get(f"{API_BASE}/checkins", timeout=20)
        if r.status_code != 200:
            st.warning("⚠️ Couldn’t load emotional data from API.")
            return

        df = pd.DataFrame(r.json())
        if df.empty:
            st.info("No emotional data yet — start logging check-ins 🌿")
            return

        # --- Ensure required fields ---
        df["tier"] = df.get("tier", "Unknown").fillna("Unknown")
        df["timestamp"] = pd.to_datetime(df.get("timestamp"), errors="coerce")
        df = df.dropna(subset=["timestamp"]).sort_values("timestamp")

        # --- Map tier → numeric score ---
        tier_map = {"Auto": 0, "Stable": 1, "At-Risk": 2, "Critical": 3, "Unknown": 0.5}
        df["score"] = df["tier"].map(tier_map)

        # --- User filter ---
        users = sorted(df["user_id"].dropna().unique().tolist())
        if not users:
            st.warning("No user data found.")
            return
        selected_user = st.selectbox("Select user to view trend", options=users)

        user_df = df[df["user_id"] == selected_user]
        if user_df.empty:
            st.info("No check-ins for this user yet.")
            return

        # --- Plot ---
        plt.figure(figsize=(10, 4))
        plt.plot(
            user_df["timestamp"],
            user_df["score"],
            marker="o",
            color="#00FFA3",
            linewidth=2,
        )
        plt.fill_between(user_df["timestamp"], user_df["score"], color="#00FFA3", alpha=0.1)

        plt.title(f"Emotional Trajectory — {selected_user}", color="#00FFA3", fontsize=14)
        plt.yticks([0, 1, 2, 3], ["Auto", "Stable", "At-Risk", "Critical"], color="white")
        plt.xticks(rotation=30, color="white")
        plt.grid(alpha=0.3)
        plt.tight_layout()
        st.pyplot(plt)

        # --- Optional summary metrics ---
        latest_tier = user_df.iloc[-1]["tier"]
        trend = "⬆️ Improving" if user_df["score"].diff().iloc[-1] < 0 else "⬇️ Declining"
        st.markdown(
            f"<p style='color:#00FFA3;'>Latest emotional state: <b>{latest_tier}</b> &nbsp;|&nbsp; Trend: <b>{trend}</b></p>",
            unsafe_allow_html=True,
        )

    except Exception as e:
        st.error(f"Error loading chart: {e}")
