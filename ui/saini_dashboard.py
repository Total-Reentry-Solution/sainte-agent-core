import streamlit as st
from components.header import render_header
from components.checkin_form import render_checkin_form
from components.history_feed import render_history_feed
from components.emotion_chart import render_emotion_chart
from components.footer import render_footer

API_BASE = "https://b6wdy7b2w0.execute-api.us-east-2.amazonaws.com/prod"
st.set_page_config(
    page_title="SAINTE Agent Core | Emotional Intelligence",
    page_icon="🧠",
    layout="wide",
)

# --- Custom Global Theme ---
st.markdown("""
<style>
body {background-color:#0A0A0A;color:white;font-family:'Inter',sans-serif;}
.block-container {padding:2rem 4rem;}
h1,h2,h3,h4,h5 {font-family:'Poppins',sans-serif;color:white;}
p,label,textarea,input {color:#B0B0B0;}
.stTabs [aria-selected="true"]{
    border-bottom:3px solid #00FFA3 !important;
    color:#00FFA3 !important;
}
.stButton>button{
    background:linear-gradient(90deg,#00FFA3,#13E3C8);
    color:black;border-radius:8px;border:none;font-weight:600;
    padding:0.6em 2em;transition:0.2s;
}
.stButton>button:hover{transform:scale(1.05);}
</style>
""", unsafe_allow_html=True)

# --- Layout ---
render_header()
tab1, tab2, tab3 = st.tabs(["💬 Check-In", "📜 History", "📈 Emotional Trends"])

with tab1:
    render_checkin_form(API_BASE)
with tab2:
    render_history_feed(API_BASE)
with tab3:
    render_emotion_chart(API_BASE)

render_footer()
