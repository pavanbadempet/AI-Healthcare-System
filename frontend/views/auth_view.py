"""
Auth View - Enterprise Split Layout
===================================
Premium, high-conversion design similar to Stripe/Auth0.
No scrollbar - everything fits in viewport.
"""
import streamlit as st
from frontend.utils import api

def render_auth_page():
    """Render a premium split-screen auth experience - NO SCROLLING."""
    
    # --- CRITICAL: FORCE NO SCROLL + VIEWPORT FIT ---
    st.markdown("""
<style>
/* FORCE VIEWPORT FIT - NO SCROLL */
html, body, [data-testid="stAppViewContainer"], .main {
    overflow: hidden !important;
    height: 100vh !important;
    max-height: 100vh !important;
}

[data-testid="stAppViewContainer"] {
    background: radial-gradient(at 0% 0%, #1E293B 0px, transparent 50%),
                radial-gradient(at 100% 0%, #3B82F6 0px, transparent 50%),
                radial-gradient(at 100% 100%, #0F172A 0px, transparent 50%),
                radial-gradient(at 0% 100%, #1E293B 0px, transparent 50%),
                #0F172A !important;
}

/* Minimal container padding */
.block-container {
    padding: 0.5rem 1rem !important;
    max-width: 100% !important;
    height: 100vh !important;
    max-height: 100vh !important;
    overflow: hidden !important;
}

/* Stat boxes - compact */
.stat-box {
    background: rgba(255,255,255,0.03); 
    backdrop-filter: blur(10px);
    padding: 0.5rem 0.75rem; 
    border-radius: 10px; 
    border: 1px solid rgba(255,255,255,0.08);
    text-align: center;
    min-width: 70px;
}
.stat-val { font-weight: 700; color: #F8FAFC; font-size: 0.85rem; }
.stat-label { font-size: 0.6rem; color: #94A3B8; }

/* Branding section - flexbox centered */
.branding-section {
    display: flex;
    flex-direction: column;
    justify-content: center;
    height: calc(100vh - 2rem);
    padding: 1rem;
}

.branding-title {
    font-family: 'Outfit', sans-serif;
    font-size: clamp(1.75rem, 4vw, 2.75rem);
    font-weight: 800;
    color: white;
    line-height: 1.1;
    margin-bottom: 0.75rem;
    letter-spacing: -1px;
}

.branding-subtitle {
    font-size: 0.85rem;
    color: #CBD5E1;
    line-height: 1.4;
    max-width: 450px;
    margin-bottom: 1.25rem;
    font-weight: 300;
}

.stats-container {
    display: flex;
    gap: 0.5rem;
}

/* Tab container - compact spacing */
.stTabs [data-baseweb="tab-list"] {
    background: transparent;
    border-bottom: 1px solid rgba(255,255,255,0.1);
    margin-bottom: 0.75rem;
    gap: 0;
}
.stTabs [data-baseweb="tab"] {
    color: #94A3B8;
    border: none;
    padding: 0.5rem 1rem;
    font-size: 0.85rem;
}
.stTabs [aria-selected="true"] {
    color: #60A5FA;
    background: transparent;
    border-bottom: 2px solid #60A5FA;
}

/* Form card - COMPACT */
div[data-testid="stForm"] {
    background: rgba(15, 23, 42, 0.6); 
    backdrop-filter: blur(16px); 
    border: 1px solid rgba(255,255,255,0.08); 
    box-shadow: 0 15px 40px -12px rgba(0,0,0,0.5);
    padding: 1rem 1.25rem;
    border-radius: 16px;
}

/* Input fields - smaller */
div[data-testid="stTextInput"] label,
div[data-testid="stPasswordInput"] label {
    font-size: 0.75rem !important;
    margin-bottom: 0.25rem !important;
}

div[data-testid="stTextInput"] input,
div[data-testid="stPasswordInput"] input {
    padding: 0.5rem 0.75rem !important;
    font-size: 0.85rem !important;
}

/* Form submit button - compact */
div[data-testid="stFormSubmitButton"] button {
    padding: 0.5rem 1rem !important;
    font-size: 0.85rem !important;
}

/* Auth form wrapper */
.auth-wrapper {
    display: flex;
    flex-direction: column;
    justify-content: center;
    height: calc(100vh - 2rem);
}

.auth-header {
    text-align: center;
    margin-bottom: 1rem;
}

.auth-header h2 {
    margin-bottom: 0.25rem;
    font-family: 'Outfit', sans-serif;
    color: white;
    font-size: 1.5rem;
}

.auth-header p {
    color: #94A3B8;
    font-size: 0.8rem;
    margin: 0;
}

.auth-footer {
    text-align: center;
    margin-top: 0.75rem;
    color: #64748B;
    font-size: 0.7rem;
    opacity: 0.7;
}
</style>
""", unsafe_allow_html=True)

    # --- SPLIT LAYOUT ---
    col1, col2 = st.columns([1.2, 1], gap="medium")
    
    # --- LEFT: BRANDING ---
    with col1:
        st.markdown("""
<div class="branding-section">
<div style="font-size: 2rem; margin-bottom: 0.75rem; filter: drop-shadow(0 0 15px rgba(59,130,246,0.3));">🏥</div>
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

    # --- RIGHT: AUTH FORM ---
    with col2:
        st.markdown("""<div class="auth-wrapper">""", unsafe_allow_html=True)
        
        st.markdown("""
<div class="auth-header">
<h2>Welcome Back</h2>
<p>Sign in to access your dashboard</p>
</div>
""", unsafe_allow_html=True)
        
        tab_login, tab_signup = st.tabs(["Sign In", "Create Account"])
        
        with tab_login:
            with st.form("login_form", border=False):
                user = st.text_input("Username", placeholder="admin")
                pwd = st.text_input("Password", type="password", placeholder="••••••")
                if st.form_submit_button("Access Dashboard →", type="primary", use_container_width=True):
                    if api.login(user, pwd):
                        st.rerun()
                        
        with tab_signup:
            with st.form("signup_form", border=False):
                fn = st.text_input("Full Name", placeholder="John Doe")
                us = st.text_input("Username", placeholder="johndoe")
                em = st.text_input("Email", placeholder="john@email.com")
                pw = st.text_input("Password", type="password")
                if st.form_submit_button("Create Account", type="primary", use_container_width=True):
                    if api.signup(us, pw, em, fn, "2000-01-01"):
                        if api.login(us, pw): st.rerun()

        st.markdown("""
<div class="auth-footer">Powered by Advanced Analytics & Secure Enclaves</div>
</div>
""", unsafe_allow_html=True)
