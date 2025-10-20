import streamlit as st
import requests, json
import time

def render_checkin_form(API_BASE: str):
    st.markdown("<h3 style='color:#00FFA3;'>🌿 Daily Emotional Check-In</h3>", unsafe_allow_html=True)
    st.caption("Your space to reflect, without judgment.")

    user_id = st.text_input("User ID", "demo_user")
    message = st.text_area("How are you feeling today?", placeholder="Be honest — what's on your mind right now?", height=120)

    if st.button("💬 Share with Saini"):
        with st.spinner("Saini is reflecting..."):
            try:
                r = requests.post(f"{API_BASE}/checkin", json={"user_id": user_id, "message": message}, timeout=25)

                # --- STEP 1: Parse top-level response ---
                if r.status_code != 200:
                    st.error(f"⚠️ Error {r.status_code}: {r.text[:200]}")
                    return

                # --- STEP 2: Extract response safely ---
                try:
                    outer = r.json()
                except Exception:
                    st.error("Response is not valid JSON.")
                    return

                # Extract body safely
                body = outer.get("body", outer)
                if isinstance(body, str):
                    try:
                        body = json.loads(body)
                    except Exception:
                        st.warning("Body is string but not valid JSON.")
                        body = {"response": body}

                if not isinstance(body, dict):
                    st.error("Unexpected response format from API.")
                    st.write(outer)
                    return

                # --- STEP 3: Access keys safely ---
                tone = body.get("tone", "gentle").capitalize()
                reflection = body.get("response") or body.get("nudge") or "No reflection available."

                color_map = {
                    "Gentle": "#00FFA3",
                    "Reassuring": "#13E3C8",
                    "Reflective": "#FFD166",
                    "Empowering": "#BB86FC",
                    "Neutral": "#B0B0B0"
                }

                st.success("✅ Reflection Recorded")
                time.sleep(0.2)

                st.markdown(f"""
                <div style='background-color:#111;padding:1em;border-radius:10px;'>
                    <p style='color:{color_map.get(tone,"#00FFA3")};font-weight:bold;'>Saini Reflection ({tone})</p>
                    <p style='color:white;font-size:16px;'>{reflection}</p>
                </div>
                """, unsafe_allow_html=True)

            except Exception as e:
                st.error(f"Connection error: {e}")
