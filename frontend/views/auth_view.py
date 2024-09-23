"""
Auth View - Minimal Form Layout
================================
3 fields only for signup to guarantee no scroll.
"""
import streamlit as st
from frontend.utils import api

def render_auth_page():
    """Auth page with minimal form - guaranteed no scroll."""
    
    st.markdown("""
<style>
/* No scrolling */
html, body, [data-testid="stAppViewContainer"], .main {
    overflow: hidden !important;
    height: 100vh !important;
}

[data-testid="stAppViewContainer"] {
    background: radial-gradient(at 0% 0%, #1E293B 0px, transparent 50%),
                radial-gradient(at 100% 0%, #3B82F6 0px, transparent 50%),
                radial-gradient(at 100% 100%, #0F172A 0px, transparent 50%),
                radial-gradient(at 0% 100%, #1E293B 0px, transparent 50%),
                #0F172A !important;
}

.block-container {
    padding: 1rem !important;
    height: 100vh !important;
    overflow: hidden !important;
}

[data-testid="stHorizontalBlock"] {
    height: calc(100vh - 2rem) !important;
    align-items: center !important;
}

/* Compact form */
div.stForm {
    padding: 0.75rem !important;
}

/* Minimal input spacing */
div[data-testid="stTextInput"] > div,
div[data-testid="stPasswordInput"] > div {
    margin-bottom: 0.4rem !important;
}

div[data-testid="stTextInput"] input,
div[data-testid="stPasswordInput"] input {
    padding: 0.4rem 0.6rem !important;
    font-size: 0.85rem !important;
}

.stTabs [data-baseweb="tab-list"] {
    background: transparent !important;
    border-bottom: 1px solid rgba(255,255,255,0.1) !important;
    margin-bottom: 0.5rem !important;
}

.stTabs [data-baseweb="tab"] {
    padding: 0.4rem 0.75rem !important;
    font-size: 0.8rem !important;
}

div[data-testid="stFormSubmitButton"] button {
    padding: 0.5rem !important;
}
</style>
""", unsafe_allow_html=True)

    col1, col2 = st.columns([1.2, 1])
    
    # Left - Branding
    with col1:
        st.markdown("""
<div style="padding: 1rem;">
    <div style="font-size: 2rem; margin-bottom: 0.5rem;">🏥</div>
    <h1 style="font-size: 2rem; margin: 0 0 0.5rem 0; color: white; line-height: 1.15;">
        The Future of<br>
        <span style="background: linear-gradient(90deg, #60A5FA, #34D399); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">AI Healthcare</span>
    </h1>
    <p style="font-size: 0.85rem; color: #94A3B8; margin: 0 0 0.75rem 0;">
        Hospital-grade predictive diagnostics. Secure data protection.
    </p>
    <div style="display: flex; gap: 0.5rem;">
        <div style="background: rgba(255,255,255,0.03); padding: 0.4rem 0.6rem; border-radius: 8px; text-align: center;">
            <div style="font-size: 0.8rem; font-weight: 700; color: #F8FAFC;">99.8%</div>
            <div style="font-size: 0.6rem; color: #64748B;">Precision</div>
        </div>
        <div style="background: rgba(255,255,255,0.03); padding: 0.4rem 0.6rem; border-radius: 8px; text-align: center;">
            <div style="font-size: 0.8rem; font-weight: 700; color: #F8FAFC;">Encrypted</div>
            <div style="font-size: 0.6rem; color: #64748B;">Data</div>
        </div>
        <div style="background: rgba(255,255,255,0.03); padding: 0.4rem 0.6rem; border-radius: 8px; text-align: center;">
            <div style="font-size: 0.8rem; font-weight: 700; color: #F8FAFC;">Global</div>
            <div style="font-size: 0.6rem; color: #64748B;">Access</div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

    # Right - Auth Form
    with col2:
        st.markdown("""
<div style="text-align: center; margin-bottom: 0.5rem;">
    <h2 style="font-size: 1.25rem; margin: 0; color: white;">Welcome Back</h2>
    <p style="font-size: 0.75rem; color: #64748B; margin: 0.25rem 0 0 0;">Sign in to your dashboard</p>
</div>
""", unsafe_allow_html=True)
        
        tab1, tab2 = st.tabs(["Sign In", "Create Account"])
        
        with tab1:
            with st.form("login", border=False):
                u = st.text_input("Username", placeholder="Enter username", label_visibility="collapsed")
                p = st.text_input("Password", type="password", placeholder="Enter password", label_visibility="collapsed")
                if st.form_submit_button("Sign In →", type="primary", width="stretch"):
                    if api.login(u, p): st.rerun()
                        
        with tab2:
            # ONLY 3 FIELDS - username, email, password (name added via profile later)
            with st.form("signup", border=False):
                us = st.text_input("Username", placeholder="Choose a username", label_visibility="collapsed")
                em = st.text_input("Email", placeholder="Your email", label_visibility="collapsed")
                pw = st.text_input("Password", type="password", placeholder="Create password", label_visibility="collapsed")
                if st.form_submit_button("Create Account", type="primary", width="stretch"):
                    if api.signup(us, pw, em, us, "2000-01-01"):  # Use username as name initially
                        if api.login(us, pw): st.rerun()
        
        st.markdown('<p style="text-align: center; font-size: 0.65rem; color: #475569; margin-top: 0.5rem;">Powered by Advanced AI</p>', unsafe_allow_html=True)
