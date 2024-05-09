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
    st.markdown(textwrap.dedent("""
    <style>
    /* 1. Global Reset for Full Screen */
    [data-testid="stAppViewContainer"] {
        background: #0F172A; /* Slate 900 */
    }
    .block-container {
        padding: 0 !important;
        max-width: 100% !important;
    }
    
    /* 2. Typography Overrides */
    h1.brand-title {
        font-family: 'Outfit', sans-serif;
        font-size: 3.5rem;
        font-weight: 800;
        line-height: 1.1;
        background: linear-gradient(to right, #fff, #94a3b8);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 1rem;
    }
    
    /* 3. Helper Classes */
    .stat-box {
        background: rgba(255,255,255,0.05); 
        padding: 1rem; 
        border-radius: 12px; 
        border: 1px solid rgba(255,255,255,0.1);
        text-align: center;
        min-width: 100px;
    }
    .stat-val { font-weight: 700; color: white; font-size: 1.2rem; }
    .stat-label { font-size: 0.8rem; color: #94A3B8; }
    </style>
    """), unsafe_allow_html=True)

    # --- SPLIT LAYOUT COLUMNS ---
    col1, col2 = st.columns([1.5, 1], gap="medium")
    
    # --- LEFT COLUMN: BRANDING ---
    with col1:
        st.markdown("""
<div style="background: radial-gradient(circle at top right, #3B82F6, #1E293B, #0F172A); height: 100vh; padding: 0 5vw; display: flex; flex-direction: column; justify-content: center; border-right: 1px solid rgba(255,255,255,0.05);">
<div style="font-size: 4rem; margin-bottom: 2rem;">🏥</div>
<h1 style="font-family: 'Outfit', sans-serif; font-size: 4rem; font-weight: 800; color: white; line-height: 1.1; margin-bottom: 1.5rem;">The Future of <br><span style="color: #60A5FA;">AI Healthcare</span></h1>
<p style="font-size: 1.2rem; color: #CBD5E1; line-height: 1.6; max-width: 600px; margin-bottom: 3rem;">Experience hospital-grade disease prediction powered by advanced machine learning. Secure, accurate, and accessible from anywhere.</p>
<div style="display: flex; gap: 1.5rem;">
<div class="stat-box"><div class="stat-val">99.8%</div><div class="stat-label">Accuracy</div></div>
<div class="stat-box"><div class="stat-val">HIPAA</div><div class="stat-label">Compliant</div></div>
<div class="stat-box"><div class="stat-val">24/7</div><div class="stat-label">AI Support</div></div>
</div>
</div>
""", unsafe_allow_html=True)

    # --- RIGHT COLUMN: AUTH FORM ---
    with col2:
        st.markdown('<div style="height: 15vh;"></div>', unsafe_allow_html=True)
        
        with st.container():
            st.markdown("""
<div style="max-width: 400px; margin: 0 auto; padding: 20px;">
<h2 style="text-align: center; margin-bottom: 2rem;">Get Started</h2>
</div>
""", unsafe_allow_html=True)
            
            tab_login, tab_signup = st.tabs(["Sign In", "Create Account"])
            
            with tab_login:
                with st.form("login_form", border=False):
                    user = st.text_input("Username", placeholder="admin")
                    pwd = st.text_input("Password", type="password", placeholder="••••••")
                    st.markdown("<br>", unsafe_allow_html=True)
                    if st.form_submit_button("Sign In →", type="primary", use_container_width=True):
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

            st.markdown("""
<div style="text-align: center; margin-top: 2rem; color: #64748B; font-size: 0.8rem;">Secure Encrypted Connection</div>
""", unsafe_allow_html=True)
