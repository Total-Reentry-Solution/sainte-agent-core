import streamlit as st, requests, pandas as pd, matplotlib.pyplot as plt

def render_emotion_chart(API_BASE):
    st.markdown("<h3 style='color:#00FFA3;'>Emotional Trend</h3>", unsafe_allow_html=True)
    try:
        r=requests.get(f"{API_BASE}/checkins")
        if r.status_code!=200: st.warning("Couldn’t load data."); return
        df=pd.DataFrame(r.json())
        if df.empty: st.info("No data to display."); return

        df["timestamp"]=pd.to_datetime(df.get("timestamp"),errors='coerce')
        df=df.dropna(subset=["timestamp"]).sort_values("timestamp")
        tier_map={"Stable":1,"At-Risk":2,"Critical":3,"Auto":0,"Unknown":0.5}
        df["score"]=df["tier"].map(tier_map)

        plt.figure(figsize=(10,4))
        plt.plot(df["timestamp"],df["score"],marker='o',color="#00FFA3",linewidth=2)
        plt.fill_between(df["timestamp"],df["score"],color="#00FFA3",alpha=.1)
        plt.yticks([0,1,2,3],["Auto","Stable","At-Risk","Critical"],color="white")
        plt.xticks(rotation=30,color="white")
        plt.title("Saini Emotional Trajectory",color="#00FFA3",fontsize=14)
        plt.grid(alpha=.3); plt.tight_layout(); st.pyplot(plt)
    except Exception as e:
        st.error(f"Error loading chart: {e}")
