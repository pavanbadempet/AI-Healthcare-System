"""
Auth View - Enterprise Split Layout
===================================
Ultra-compact design - NO SCROLLING ALLOWED.
"""
import streamlit as st
from frontend.utils import api

def render_auth_page():
    """Render auth page that MUST fit in viewport."""
    
    # NUCLEAR OPTION: Force everything to fit
    st.markdown("""
<style>
/* ========== FORCE NO SCROLL - NUCLEAR ========== */
html, body {
    overflow: hidden !important;
    height: 100vh !important;
    max-height: 100vh !important;
    margin: 0 !important;
    padding: 0 !important;
}

[data-testid="stAppViewContainer"],
[data-testid="stAppViewContainer"] > .main,
.stApp {
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

/* Remove ALL padding from container */
.block-container {
    padding: 0 !important;
    max-width: 100% !important;
    height: 100vh !important;
    overflow: hidden !important;
}

/* Remove gap from columns */
[data-testid="stHorizontalBlock"] {
    gap: 1rem !important;
    height: 100vh !important;
    align-items: stretch !important;
    padding: 0.5rem 1rem !important;
}

[data-testid="stColumn"] {
    height: 100% !important;
    display: flex !important;
    flex-direction: column !important;
    justify-content: center !important;
}

/* ========== LEFT COLUMN STYLES ========== */
.brand-container {
    padding: 1rem;
}

.brand-icon {
    font-size: 1.75rem;
    margin-bottom: 0.5rem;
    filter: drop-shadow(0 0 15px rgba(59,130,246,0.3));
}

.brand-title {
    font-family: 'Outfit', sans-serif;
    font-size: clamp(1.5rem, 3vw, 2.25rem);
    font-weight: 800;
    color: white;
    line-height: 1.1;
    margin-bottom: 0.5rem;
}

.brand-subtitle {
    font-size: 0.8rem;
    color: #CBD5E1;
    line-height: 1.3;
    margin-bottom: 0.75rem;
}

.stats-row {
    display: flex;
    gap: 0.5rem;
}

.stat-item {
    background: rgba(255,255,255,0.03);
    padding: 0.4rem 0.6rem;
    border-radius: 8px;
    border: 1px solid rgba(255,255,255,0.08);
    text-align: center;
}

.stat-val {
    font-weight: 700;
    color: #F8FAFC;
    font-size: 0.75rem;
}

.stat-lbl {
    font-size: 0.55rem;
    color: #94A3B8;
}

/* ========== RIGHT COLUMN - AUTH FORM ========== */
.auth-box {
    padding: 0.75rem;
}

.auth-header {
    text-align: center;
    margin-bottom: 0.5rem;
}

.auth-header h2 {
    font-size: 1.25rem;
    margin: 0 0 0.25rem 0;
    color: white;
}

.auth-header p {
    font-size: 0.75rem;
    color: #94A3B8;
    margin: 0;
}

/* Tabs - ultra compact */
.stTabs {
    margin-top: 0 !important;
}

.stTabs [data-baseweb="tab-list"] {
    background: transparent !important;
    border-bottom: 1px solid rgba(255,255,255,0.1) !important;
    margin-bottom: 0.5rem !important;
    gap: 0 !important;
}

.stTabs [data-baseweb="tab"] {
    color: #94A3B8 !important;
    padding: 0.4rem 0.75rem !important;
    font-size: 0.8rem !important;
}

.stTabs [aria-selected="true"] {
    color: #60A5FA !important;
    border-bottom: 2px solid #60A5FA !important;
}

/* Form - MINIMAL padding */
div[data-testid="stForm"] {
    background: rgba(15, 23, 42, 0.5) !important;
    backdrop-filter: blur(12px) !important;
    border: 1px solid rgba(255,255,255,0.06) !important;
    padding: 0.75rem !important;
    border-radius: 12px !important;
    box-shadow: 0 10px 30px -10px rgba(0,0,0,0.4) !important;
}

/* Input labels - tiny */
div[data-testid="stTextInput"] label,
div[data-testid="stPasswordInput"] label {
    font-size: 0.7rem !important;
    margin-bottom: 0.15rem !important;
    color: #94A3B8 !important;
}

/* Input fields - compact */
div[data-testid="stTextInput"] > div,
div[data-testid="stPasswordInput"] > div {
    margin-bottom: 0.4rem !important;
}

div[data-testid="stTextInput"] input,
div[data-testid="stPasswordInput"] input {
    padding: 0.4rem 0.6rem !important;
    font-size: 0.8rem !important;
    border-radius: 8px !important;
    background: rgba(15, 23, 42, 0.6) !important;
    border: 1px solid rgba(148, 163, 184, 0.15) !important;
}

/* Submit button - compact */
div[data-testid="stFormSubmitButton"] {
    margin-top: 0.25rem !important;
}

div[data-testid="stFormSubmitButton"] button {
    padding: 0.45rem 0.75rem !important;
    font-size: 0.8rem !important;
    border-radius: 8px !important;
}

.auth-footer {
    text-align: center;
    margin-top: 0.5rem;
    font-size: 0.65rem;
    color: #475569;
}
</style>
""", unsafe_allow_html=True)

    # Two-column layout
    col1, col2 = st.columns([1.2, 1])
    
    # LEFT: Branding
    with col1:
        st.markdown("""
<div class="brand-container">
    <div class="brand-icon">🏥</div>
    <h1 class="brand-title">
        The Future of<br>
        <span style="background: linear-gradient(90deg, #60A5FA, #34D399); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">AI Healthcare</span>
    </h1>
    <p class="brand-subtitle">
        Hospital-grade predictive diagnostics. Secure data protection. Real-time AI analysis.
    </p>
    <div class="stats-row">
        <div class="stat-item"><div class="stat-val">99.8%</div><div class="stat-lbl">Precision</div></div>
        <div class="stat-item"><div class="stat-val">Encrypted</div><div class="stat-lbl">Data</div></div>
        <div class="stat-item"><div class="stat-val">Global</div><div class="stat-lbl">Access</div></div>
    </div>
</div>
""", unsafe_allow_html=True)

    # RIGHT: Auth Form
    with col2:
        st.markdown("""
<div class="auth-box">
    <div class="auth-header">
        <h2>Welcome Back</h2>
        <p>Sign in to access your dashboard</p>
    </div>
</div>
""", unsafe_allow_html=True)
        
        tab_login, tab_signup = st.tabs(["Sign In", "Create Account"])
        
        with tab_login:
            with st.form("login_form", border=False):
                user = st.text_input("Username", placeholder="admin", label_visibility="collapsed")
                pwd = st.text_input("Password", type="password", placeholder="Password", label_visibility="collapsed")
                st.form_submit_button("Sign In →", type="primary", use_container_width=True)
                if user and pwd:
                    if api.login(user, pwd):
                        st.rerun()
                        
        with tab_signup:
            with st.form("signup_form", border=False):
                fn = st.text_input("Full Name", placeholder="Full Name", label_visibility="collapsed")
                us = st.text_input("Username", placeholder="Username", label_visibility="collapsed")
                em = st.text_input("Email", placeholder="Email", label_visibility="collapsed")
                pw = st.text_input("Password", type="password", placeholder="Password", label_visibility="collapsed")
                submitted = st.form_submit_button("Create Account", type="primary", use_container_width=True)
                if submitted and us and pw and em:
                    if api.signup(us, pw, em, fn, "2000-01-01"):
                        if api.login(us, pw):
                            st.rerun()

        st.markdown('<div class="auth-footer">Powered by Advanced Analytics</div>', unsafe_allow_html=True)
