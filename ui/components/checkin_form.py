import streamlit as st
import requests, json

def render_checkin_form(API_BASE:str):
    st.markdown("<h3 style='color:#00FFA3;'>Daily Check-In</h3>", unsafe_allow_html=True)
    user_id = st.text_input("User ID", "demo_user")
    message = st.text_area("How are you feeling today?",
                           "Feeling okay but a bit tired.",
                           height=120)

    if st.button("Submit Check-In"):
        with st.spinner("Analyzing your reflection…"):
            try:
                r = requests.post(f"{API_BASE}/checkin",
                                  json={"user_id": user_id, "message": message})
                if r.status_code == 200:
                    res = r.json().get("body")
                    if isinstance(res, str): res = json.loads(res)

                    tone = res.get("tone", "gentle").capitalize()
                    reflection = res.get("nudge") or res.get("response","")

                    color_map = {
                        "Gentle":"#00FFA3",
                        "Reassuring":"#13E3C8",
                        "Reflective":"#FFD166",
                        "Empowering":"#BB86FC",
                        "Neutral":"#B0B0B0"
                    }
                    tone_color = color_map.get(tone,"#00FFA3")

                    st.success("✅ Reflection Recorded")
                    st.markdown(f"""
                    <div style='background-color:#111;padding:1em;border-radius:10px;'>
                        <p style='color:{tone_color};font-weight:bold;'>Saini Reflection ({tone})</p>
                        <p style='color:white;font-size:16px;'>{reflection}</p>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.error(f"Error {r.status_code}: Unable to connect to API.")
            except Exception as e:
                st.error(f"Connection error: {e}")
