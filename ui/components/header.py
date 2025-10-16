import streamlit as st
from pathlib import Path
from PIL import Image, ImageDraw

def render_header():
    assets_dir = Path(__file__).resolve().parent.parent / "assets"
    logo_svg = assets_dir / "saint.svg"

    st.markdown("<div style='text-align:center;'>", unsafe_allow_html=True)

    # --- Try to load SVG ---
    if logo_svg.exists():
        try:
            with open(logo_svg, "r", encoding="utf-8") as f:
                svg_code = f.read()
            st.image(str(logo_svg), width=160)  # Streamlit 1.36+ supports SVG directly
        except Exception as e:
            st.markdown(f"<p style='color:#ff5555;'>⚠️ Error loading SVG: {e}</p>", unsafe_allow_html=True)
    else:
        # --- Fallback simple Sainte banner ---
        img = Image.new("RGB", (400, 120), color="#000000")
        draw = ImageDraw.Draw(img)
        draw.text((60, 40), "SAINTE", fill="#00FFA3")
        st.image(img, width=160)

    # --- Title & subtitle ---
    st.markdown("""
        <h1 style='color:#00FFA3;font-size:36px;font-weight:700;margin-top:0;'>SAINTE Agent Core</h1>
        <p style='color:#B0B0B0;'>Empathetic AI for Trauma-Informed Care | Built on AWS Bedrock</p>
        <hr style='border: 1px solid #1C1C1C; margin: 2em 0;'/>
    """, unsafe_allow_html=True)
