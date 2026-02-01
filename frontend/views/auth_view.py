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
    padding-top: 2rem !important;
    padding-bottom: 1rem !important;
    max-width: 100% !important;
}

/* Helper Classes */
.stat-box {
    background: rgba(255,255,255,0.03); 
    backdrop-filter: blur(10px);
    padding: 0.8rem; 
    border-radius: 12px; 
    border: 1px solid rgba(255,255,255,0.08);
    text-align: center;
    min-width: 80px;
    flex: 1;
    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
}
.stat-val { font-weight: 700; color: #F8FAFC; font-size: 1rem; }
.stat-label { font-size: 0.7rem; color: #94A3B8; }

/* Stats container - responsive flex */
.stats-container {
    display: flex;
    gap: 0.75rem;
    flex-wrap: wrap;
    justify-content: flex-start;
}

/* Branding section - responsive */
.branding-section {
    padding: 2rem 3vw;
    display: flex;
    flex-direction: column;
    justify-content: center;
    min-height: 50vh;
}

.branding-title {
    font-family: 'Outfit', sans-serif;
    font-size: clamp(2rem, 5vw, 3.5rem);
    font-weight: 800;
    color: white;
    line-height: 1.1;
    margin-bottom: 1rem;
    letter-spacing: -1px;
}

.branding-subtitle {
    font-size: clamp(0.9rem, 2vw, 1rem);
    color: #CBD5E1;
    line-height: 1.5;
    max-width: 550px;
    margin-bottom: 2rem;
    font-weight: 300;
}

/* Mobile Responsive */
@media only screen and (max-width: 768px) {
    .branding-section {
        padding: 1.5rem 1rem;
        min-height: auto;
        text-align: center;
    }
    
    .branding-subtitle {
        max-width: 100%;
    }
    
    .stats-container {
        justify-content: center;
    }
    
    .stat-box {
        min-width: 70px;
        padding: 0.6rem;
    }
    
    .stat-val {
        font-size: 0.9rem;
    }
}
</style>
""", unsafe_allow_html=True)

    # --- SPLIT CONTENT (Floating on same bg) ---
    col1, col2 = st.columns([1.3, 1], gap="large")
    
    # --- LEFT COLUMN: BRANDING ---
    with col1:
        st.markdown("""
<div class="branding-section">
<div style="font-size: 2.5rem; margin-bottom: 1rem; filter: drop-shadow(0 0 20px rgba(59,130,246,0.3));">🏥</div>
<h1 class="branding-title">
The Future of <br>
<span style="background: linear-gradient(90deg, #60A5FA, #34D399); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">AI Healthcare</span>
</h1>
<p class="branding-subtitle">
Hospital-grade predictive diagnostics. Secure data protection. 
Real-time analysis powered by next-gen neural networks.
</p>
<div class="stats-container">
<div class="stat-box"><div class="stat-val">99.8%</div><div class="stat-label">Precision</div></div>
<div class="stat-box"><div class="stat-val">Encrypted</div><div class="stat-label">Data</div></div>
<div class="stat-box"><div class="stat-val">Global</div><div class="stat-label">Access</div></div>
</div>
</div>
""", unsafe_allow_html=True)

    # --- RIGHT COLUMN: AUTH FORM ---
    with col2:
        # st.markdown('<div style="height: 15vh;"></div>', unsafe_allow_html=True)
        
        with st.container():
            # Header Text (No Card Style)
            st.markdown("""
<div style="text-align: center; margin-bottom: 2rem;">
<h2 style="margin-bottom: 0.5rem; font-family: 'Outfit', sans-serif; color: white;">Welcome Back</h2>
<p style="color: #94A3B8; font-size: 0.9rem;">Sign in to access your dashboard</p>
</div>
""", unsafe_allow_html=True)
            
            # Styles for Tabs to match Glass
            st.markdown("""
<style>
/* Make Tabs Transparent & Integrated */
.stTabs [data-baseweb="tab-list"] {
    background: transparent;
    border-bottom: 1px solid rgba(255,255,255,0.1);
    margin-bottom: 1rem;
}
.stTabs [data-baseweb="tab"] {
    color: #94A3B8;
    border: none;
}
.stTabs [aria-selected="true"] {
    color: #60A5FA;
    background: transparent;
    border-bottom: 2px solid #60A5FA;
}
/* Ensure Form is the Glass Card */
div[data-testid="stForm"] {
    background: rgba(15, 23, 42, 0.6); 
    backdrop-filter: blur(16px); 
    border: 1px solid rgba(255,255,255,0.08); 
    box-shadow: 0 25px 50px -12px rgba(0,0,0,0.5);
    padding: 2rem;
    border-radius: 20px;
}
</style>
""", unsafe_allow_html=True)
            
            tab_login, tab_signup = st.tabs(["Sign In", "Create Account"])
            
            with tab_login:
                with st.form("login_form", border=False):
                    user = st.text_input("Username", placeholder="admin")
                    pwd = st.text_input("Password", type="password", placeholder="••••••")
                    st.markdown("<div style='height: 10px'></div>", unsafe_allow_html=True)
                    if st.form_submit_button("Access Dashboard →", type="primary", use_container_width=True):
                        if api.login(user, pwd):
                            st.rerun()
                            
            with tab_signup:
                with st.form("signup_form", border=False):
                    fn = st.text_input("Full Name", placeholder="John Doe")
                    us = st.text_input("Username", placeholder="johndoe")
                    em = st.text_input("Email", placeholder="john@email.com")
                    pw = st.text_input("Password", type="password")
                    st.markdown("<div style='height: 10px'></div>", unsafe_allow_html=True)
                    if st.form_submit_button("Create Account", type="primary", use_container_width=True):
                        if api.signup(us, pw, em, fn, "2000-01-01"):
                            if api.login(us, pw): st.rerun()

            st.markdown("""
<div style="text-align: center; margin-top: 1.5rem; color: #64748B; font-size: 0.8rem; opacity: 0.7;">
Powered by Advanced Analytics & Secure Enclaves
</div>
""", unsafe_allow_html=True)
