import streamlit as st

def render_footer():
    st.markdown("""
        <hr style='border: 1px solid #1C1C1C;'/>
        <div style='text-align:center;color:#B0B0B0;padding:1em;'>
            <p>© 2025 SAINTE | Powered by AWS Bedrock | Built with 💚 for Trauma-Informed Care</p>
            <p style='font-size:13px;'>
                <a href='https://joinsainte.com' style='color:#00FFA3;text-decoration:none;'>joinsainte.com</a> 
                | <a href='#' style='color:#B0B0B0;'>Privacy Policy</a> 
                | <a href='#' style='color:#B0B0B0;'>Terms of Service</a>
            </p>
        </div>
    """, unsafe_allow_html=True)
