import streamlit as st
import pandas as pd
from frontend.utils import api

def render_auth_page():
    # PREMIUM SPLIT LAYOUT
    hero_col, auth_col = st.columns([1.4, 1], gap="large")
    
    with hero_col:
        hero_html = (
            '<div style="padding-top: 50px; padding-right: 20px; border-right: 1px solid #333;">'
            '<h1 style="font-size: 3.5rem; font-weight: 800; background: -webkit-linear-gradient(0deg, #00d2ff, #3a7bd5); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">Future Health<br>Is Here.</h1>'
            '<p style="font-size: 1.2rem; color: #a0aab9; margin-top: 20px; line-height: 1.6;">'
            'Experience the power of <strong>AI-driven diagnostics</strong>. '
            'Monitor your vitals, predict potential risks, and safeguard your future with our '
            'enterprise-grade healthcare system.'
            '</p>'
            '<div style="display: flex; gap: 15px; margin-top: 30px;">'
            '<span style="background: #1e232b; padding: 10px 20px; border-radius: 20px; color: #00d2ff; border: 1px solid #00d2ff33;">&#128737; Secure</span>'
            '<span style="background: #1e232b; padding: 10px 20px; border-radius: 20px; color: #00d2ff; border: 1px solid #00d2ff33;">&#9889; Real-time</span>'
            '<span style="background: #1e232b; padding: 10px 20px; border-radius: 20px; color: #00d2ff; border: 1px solid #00d2ff33;">&#129302; AI Powered</span>'
            '</div>'
            '</div>'
        )
        st.markdown(hero_html, unsafe_allow_html=True)

    with auth_col:
        st.markdown("<br><br>", unsafe_allow_html=True)
        # Using emoji titles as requested in original design
        auth_tabs = st.tabs(["🔐 Login", "📝 Sign Up"])
        
        with auth_tabs[0]:
            st.markdown("### Welcome Back")
            with st.form("login_form", border=False):
                username = st.text_input("Username", placeholder="Enter your username")
                password = st.text_input("Password", type="password", placeholder="Enter your password")
                
                st.markdown("<br>", unsafe_allow_html=True)
                if st.form_submit_button("Access Portal", type="primary", use_container_width=True):
                    if username and password:
                        with st.spinner("Authenticating..."):
                            if api.login(username, password):
                                st.success("Login Successful!")
                                st.rerun()
                    else:
                        st.warning("Please enter both username and password.")

        with auth_tabs[1]:
            st.markdown("### Create Account")
            with st.form("signup_form", border=False):
                new_fullname = st.text_input("Full Name")
                new_email = st.text_input("Email Address")
                new_dob = st.date_input("Date of Birth", value=None, min_value=pd.to_datetime("1900-01-01"), max_value=pd.to_datetime("today"))
                
                st.caption("Secure Credentials")
                new_user = st.text_input("Username")
                new_pass = st.text_input("Password", type="password", help="Must be 8+ chars (letters & numbers).")
                
                st.markdown("<br>", unsafe_allow_html=True)
                
                # MEDICAL CONSENT (Mandatory)
                terms_agreed = st.checkbox("I agree to the Terms of Service & Medical Disclaimer", help="You must agree that this AI is not a doctor and you will consult a professional for medical needs.")
                
                if st.form_submit_button("Register Account", use_container_width=True):
                    missing = []
                    if not new_user: missing.append("Username")
                    if not new_pass: missing.append("Password")
                    if not new_fullname: missing.append("Full Name")
                    if not new_email: missing.append("Email")
                    if not new_dob: missing.append("Date of Birth")
                    
                    if not terms_agreed:
                        st.error("⚠️ You must agree to the Terms & Conditions to proceed.")
                    elif not missing:
                        with st.spinner("Creating secure profile..."):
                            if api.signup(new_user, new_pass, new_email, new_fullname, new_dob):
                                st.success("Account created successfully! Please switch to Login tab.")
                            # Error handled in api.signup
                    else:
                        st.warning(f"Missing fields: {', '.join(missing)}")
