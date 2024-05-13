"""
Auth View - Enterprise Split Layout
===================================
Premium, high-conversion design similar to Stripe/Auth0.
"""
import streamlit as st
import textwrap
import pandas as pd
from frontend.utils import api

def render_auth_page():
    """Render a premium split-screen auth experience."""
    
    # --- GLOBAL STYLES & LAYOUT RESET ---
    st.markdown("""
<style>
/* 1. Global Unified Background (Mesh Gradient) */
[data-testid="stAppViewContainer"] {
    background: radial-gradient(at 0% 0%, #1E293B 0px, transparent 50%),
                radial-gradient(at 100% 0%, #3B82F6 0px, transparent 50%),
                radial-gradient(at 100% 100%, #0F172A 0px, transparent 50%),
                radial-gradient(at 0% 100%, #1E293B 0px, transparent 50%),
                #0F172A !important;
}

/* Remove Padding */
.block-container {
    padding: 0 !important;
    max-width: 100% !important;
}

/* Helper Classes */
.stat-box {
    background: rgba(255,255,255,0.03); 
    backdrop-filter: blur(10px);
    padding: 1rem; 
    border-radius: 12px; 
    border: 1px solid rgba(255,255,255,0.08);
    text-align: center;
    min-width: 100px;
    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
}
.stat-val { font-weight: 700; color: #F8FAFC; font-size: 1.2rem; }
.stat-label { font-size: 0.8rem; color: #94A3B8; }
</style>
""", unsafe_allow_html=True)

    # --- SPLIT CONTENT (Floating on same bg) ---
    col1, col2 = st.columns([1.3, 1], gap="large")
    
    # --- LEFT COLUMN: BRANDING ---
    with col1:
        st.markdown("""
<div style="height: 100vh; padding: 0 5vw; display: flex; flex-direction: column; justify-content: center;">
<div style="font-size: 4rem; margin-bottom: 2rem; filter: drop-shadow(0 0 20px rgba(59,130,246,0.3));">🏥</div>
<h1 style="font-family: 'Outfit', sans-serif; font-size: 4.5rem; font-weight: 800; color: white; line-height: 1.05; margin-bottom: 1.5rem; letter-spacing: -2px;">
The Future of <br>
<span style="background: linear-gradient(90deg, #60A5FA, #34D399); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">AI Healthcare</span>
</h1>
<p style="font-size: 1.25rem; color: #CBD5E1; line-height: 1.6; max-width: 550px; margin-bottom: 3rem; font-weight: 300;">
Hospital-grade predictive diagnostics. HIPAA compliant security. 
Real-time analysis powered by next-gen neural networks.
</p>
<div style="display: flex; gap: 1.5rem;">
<div class="stat-box"><div class="stat-val">99.8%</div><div class="stat-label">Precision</div></div>
<div class="stat-box"><div class="stat-val">HIPAA</div><div class="stat-label">Secure</div></div>
<div class="stat-box"><div class="stat-val">24/7</div><div class="stat-label">Monitor</div></div>
</div>
</div>
""", unsafe_allow_html=True)

    # --- RIGHT COLUMN: AUTH FORM ---
    with col2:
        st.markdown('<div style="height: 20vh;"></div>', unsafe_allow_html=True)
        
        with st.container():
            # Glass Card Style injected directly via Markdown wrapper around form? 
            # No, streamlits form container is separate. We visually wrap it.
            st.markdown("""
<div style="background: rgba(15, 23, 42, 0.6); backdrop-filter: blur(16px); padding: 40px; border-radius: 24px; border: 1px solid rgba(255,255,255,0.08); box-shadow: 0 25px 50px -12px rgba(0,0,0,0.5); margin-right: 5vw;">
<h2 style="text-align: center; margin-bottom: 0.5rem; font-family: 'Outfit', sans-serif;">Welcome</h2>
<p style="text-align: center; color: #64748B; font-size: 0.9rem; margin-bottom: 2rem;">Sign in to access your dashboard</p>
""", unsafe_allow_html=True)
            
            tab_login, tab_signup = st.tabs(["Sign In", "Create Account"])
            
            with tab_login:
                with st.form("login_form", border=False):
                    user = st.text_input("Username", placeholder="admin")
                    pwd = st.text_input("Password", type="password", placeholder="••••••")
                    st.markdown("<br>", unsafe_allow_html=True)
                    if st.form_submit_button("Access Dashboard →", type="primary", use_container_width=True):
                        if api.login(user, pwd):
                            st.rerun()
                            
            with tab_signup:
                with st.form("signup_form", border=False):
                    fn = st.text_input("Full Name", placeholder="John Doe")
                    us = st.text_input("Username", placeholder="johndoe")
                    em = st.text_input("Email", placeholder="john@email.com")
                    pw = st.text_input("Password", type="password")
                    st.markdown("<br>", unsafe_allow_html=True)
                    if st.form_submit_button("Create Account", type="primary", use_container_width=True):
                        if api.signup(us, pw, em, fn, "2000-01-01"):
                            if api.login(us, pw): st.rerun()

            st.markdown("</div>", unsafe_allow_html=True) # Close Glass Card
            
            st.markdown("""
<div style="text-align: center; margin-top: 1.5rem; color: #64748B; font-size: 0.8rem; opacity: 0.7;">
Powered by Neural Networks & Secure Enclaves
</div>
""", unsafe_allow_html=True)
