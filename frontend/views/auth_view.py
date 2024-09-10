"""
Auth View - NO SCROLL VERSION
==============================
Uses auth-page class to override global styles.
"""
import streamlit as st
from frontend.utils import api

def render_auth_page():
    """Auth page that fits in viewport - no scrollbar."""
    
    # Add auth-page marker and override ALL global styles
    st.markdown("""
<style>
/* ======== AUTH PAGE OVERRIDES - HIGHEST PRIORITY ======== */

/* Force viewport fit */
.auth-page-active,
.auth-page-active html,
.auth-page-active body,
.auth-page-active [data-testid="stAppViewContainer"],
.auth-page-active .main,
.auth-page-active .stApp {
    overflow: hidden !important;
    height: 100vh !important;
    max-height: 100vh !important;
}

/* Also apply without class in case it doesn't work */
html, body {
    overflow: hidden !important;
    height: 100vh !important;
    max-height: 100vh !important;
}

[data-testid="stAppViewContainer"] {
    overflow: hidden !important;
    height: 100vh !important;
    background: radial-gradient(at 0% 0%, #1E293B 0px, transparent 50%),
                radial-gradient(at 100% 0%, #3B82F6 0px, transparent 50%),
                radial-gradient(at 100% 100%, #0F172A 0px, transparent 50%),
                radial-gradient(at 0% 100%, #1E293B 0px, transparent 50%),
                #0F172A !important;
}

.main .block-container {
    padding: 0.5rem 1rem !important;
    max-width: 100% !important;
    height: 100vh !important;
    max-height: 100vh !important;
    overflow: hidden !important;
}

/* Override global form padding - THIS IS KEY */
.main div.stForm,
div[data-testid="stForm"] {
    padding: 0.6rem 0.8rem !important;
    border-radius: 12px !important;
    background: rgba(15, 23, 42, 0.5) !important;
    border: 1px solid rgba(255,255,255,0.06) !important;
    box-shadow: 0 8px 24px -8px rgba(0,0,0,0.4) !important;
}

/* Columns full height */
[data-testid="stHorizontalBlock"] {
    height: calc(100vh - 1rem) !important;
    gap: 0.5rem !important;
    padding: 0 !important;
    align-items: center !important;
}

[data-testid="stColumn"] {
    display: flex !important;
    flex-direction: column !important;
    justify-content: center !important;
}

/* Tabs - compact */
.stTabs [data-baseweb="tab-list"] {
    background: transparent !important;
    border-bottom: 1px solid rgba(255,255,255,0.1) !important;
    margin-bottom: 0.4rem !important;
}

.stTabs [data-baseweb="tab"] {
    padding: 0.35rem 0.6rem !important;
    font-size: 0.75rem !important;
    color: #94A3B8 !important;
}

.stTabs [aria-selected="true"] {
    color: #60A5FA !important;
    border-bottom: 2px solid #60A5FA !important;
}

/* Input containers - minimal spacing */
div[data-testid="stTextInput"],
div[data-testid="stPasswordInput"] {
    margin-bottom: 0.3rem !important;
}

div[data-testid="stTextInput"] > div > div,
div[data-testid="stPasswordInput"] > div > div {
    margin-bottom: 0 !important;
}

/* Input fields */  
div[data-testid="stTextInput"] input,
div[data-testid="stPasswordInput"] input {
    padding: 0.35rem 0.5rem !important;
    font-size: 0.8rem !important;
    border-radius: 6px !important;
}

/* Hide labels */
div[data-testid="stTextInput"] label,
div[data-testid="stPasswordInput"] label {
    display: none !important;
}

/* Submit button */
div[data-testid="stFormSubmitButton"] {
    margin-top: 0.2rem !important;
}

div[data-testid="stFormSubmitButton"] button {
    padding: 0.4rem 0.6rem !important;
    font-size: 0.8rem !important;
    border-radius: 8px !important;
    min-height: 0 !important;
}

/* Branding styles */
.auth-brand {
    padding: 0.5rem 1rem;
}

.auth-brand h1 {
    font-size: clamp(1.4rem, 2.5vw, 2rem) !important;
    line-height: 1.15 !important;
    margin: 0 0 0.4rem 0 !important;
    color: white !important;
}

.auth-brand p {
    font-size: 0.75rem !important;
    color: #94A3B8 !important;
    margin: 0 0 0.5rem 0 !important;
    line-height: 1.3 !important;
}

.auth-stats {
    display: flex;
    gap: 0.4rem;
}

.auth-stat {
    background: rgba(255,255,255,0.03);
    padding: 0.3rem 0.5rem;
    border-radius: 6px;
    border: 1px solid rgba(255,255,255,0.06);
    text-align: center;
}

.auth-stat-val {
    font-size: 0.7rem;
    font-weight: 700;
    color: #F8FAFC;
}

.auth-stat-lbl {
    font-size: 0.5rem;
    color: #64748B;
}

.auth-header {
    text-align: center;
    margin-bottom: 0.4rem;
}

.auth-header h2 {
    font-size: 1.1rem !important;
    margin: 0 !important;
    color: white !important;
}

.auth-header p {
    font-size: 0.7rem !important;
    color: #64748B !important;
    margin: 0.15rem 0 0 0 !important;
}
</style>
<script>document.body.classList.add('auth-page-active');</script>
""", unsafe_allow_html=True)

    col1, col2 = st.columns([1.15, 1])
    
    with col1:
        st.markdown("""
<div class="auth-brand">
    <div style="font-size: 1.5rem; margin-bottom: 0.4rem;">🏥</div>
    <h1>The Future of<br><span style="background: linear-gradient(90deg, #60A5FA, #34D399); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">AI Healthcare</span></h1>
    <p>Hospital-grade diagnostics. Secure data. Real-time AI analysis.</p>
    <div class="auth-stats">
        <div class="auth-stat"><div class="auth-stat-val">99.8%</div><div class="auth-stat-lbl">Precision</div></div>
        <div class="auth-stat"><div class="auth-stat-val">Encrypted</div><div class="auth-stat-lbl">Data</div></div>
        <div class="auth-stat"><div class="auth-stat-val">Global</div><div class="auth-stat-lbl">Access</div></div>
    </div>
</div>
""", unsafe_allow_html=True)

    with col2:
        st.markdown("""<div class="auth-header"><h2>Welcome Back</h2><p>Sign in to your dashboard</p></div>""", unsafe_allow_html=True)
        
        tab1, tab2 = st.tabs(["Sign In", "Create Account"])
        
        with tab1:
            with st.form("login", border=False):
                u = st.text_input("u", placeholder="Username", label_visibility="collapsed")
                p = st.text_input("p", type="password", placeholder="Password", label_visibility="collapsed")
                if st.form_submit_button("Sign In →", type="primary", use_container_width=True):
                    if api.login(u, p): st.rerun()
                        
        with tab2:
            with st.form("signup", border=False):
                fn = st.text_input("fn", placeholder="Full Name", label_visibility="collapsed")
                us = st.text_input("us", placeholder="Username", label_visibility="collapsed")
                em = st.text_input("em", placeholder="Email", label_visibility="collapsed")
                pw = st.text_input("pw", type="password", placeholder="Password", label_visibility="collapsed")
                if st.form_submit_button("Create Account", type="primary", use_container_width=True):
                    if api.signup(us, pw, em, fn, "2000-01-01"):
                        if api.login(us, pw): st.rerun()

        st.markdown('<p style="text-align:center;font-size:0.6rem;color:#475569;margin-top:0.3rem;">Powered by AI</p>', unsafe_allow_html=True)
