"""
Auth View - Compact Single Screen
=================================
No scrollbar. Everything fits in viewport.
"""
import streamlit as st
from frontend.utils import api

def render_auth_page():
    """Auth page - fits in single viewport."""
    
    st.markdown("""
<style>
/* Force no scroll */
html, body, [data-testid="stAppViewContainer"], .main, .stApp {
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

.block-container {
    padding: 0.5rem 1rem !important;
    height: 100vh !important;
    max-height: 100vh !important;
    overflow: hidden !important;
}

[data-testid="stHorizontalBlock"] {
    height: calc(100vh - 1rem) !important;
    align-items: center !important;
}

/* Auth form - extra compact */
div.stForm {
    padding: 0.6rem !important;
    border-radius: 10px !important;
}

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
    background: transparent !important;
    border-bottom: 1px solid rgba(255,255,255,0.1) !important;
    margin-bottom: 0.4rem !important;
}

.stTabs [data-baseweb="tab"] {
    padding: 0.3rem 0.5rem !important;
    font-size: 0.75rem !important;
}

/* Inputs - minimal */
div[data-testid="stTextInput"],
div[data-testid="stPasswordInput"] {
    margin-bottom: 0.25rem !important;
}

div[data-testid="stTextInput"] input,
div[data-testid="stPasswordInput"] input {
    padding: 0.35rem 0.5rem !important;
    font-size: 0.8rem !important;
}

div[data-testid="stFormSubmitButton"] button {
    padding: 0.4rem !important;
    font-size: 0.8rem !important;
}
</style>
""", unsafe_allow_html=True)

    col1, col2 = st.columns([1.1, 1])
    
    with col1:
        st.markdown("""
<div style="padding: 0.5rem;">
    <div style="font-size: 1.5rem; margin-bottom: 0.4rem;">🏥</div>
    <h1 style="font-size: clamp(1.3rem, 2.5vw, 1.8rem); margin: 0 0 0.3rem 0; color: white; line-height: 1.15;">
        The Future of<br>
        <span style="background: linear-gradient(90deg, #60A5FA, #34D399); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">AI Healthcare</span>
    </h1>
    <p style="font-size: 0.75rem; color: #94A3B8; margin: 0 0 0.5rem 0; line-height: 1.3;">
        Hospital-grade diagnostics. Secure data. Real-time AI.
    </p>
    <div style="display: flex; gap: 0.4rem;">
        <div style="background: rgba(255,255,255,0.03); padding: 0.3rem 0.5rem; border-radius: 6px; text-align: center;">
            <div style="font-size: 0.7rem; font-weight: 700; color: #F8FAFC;">99.8%</div>
            <div style="font-size: 0.5rem; color: #64748B;">Precision</div>
        </div>
        <div style="background: rgba(255,255,255,0.03); padding: 0.3rem 0.5rem; border-radius: 6px; text-align: center;">
            <div style="font-size: 0.7rem; font-weight: 700; color: #F8FAFC;">Encrypted</div>
            <div style="font-size: 0.5rem; color: #64748B;">Data</div>
        </div>
        <div style="background: rgba(255,255,255,0.03); padding: 0.3rem 0.5rem; border-radius: 6px; text-align: center;">
            <div style="font-size: 0.7rem; font-weight: 700; color: #F8FAFC;">Global</div>
            <div style="font-size: 0.5rem; color: #64748B;">Access</div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

    with col2:
        st.markdown('<div style="text-align: center; margin-bottom: 0.3rem;"><h2 style="font-size: 1rem; margin: 0; color: white;">Welcome Back</h2><p style="font-size: 0.7rem; color: #64748B; margin: 0;">Sign in to your dashboard</p></div>', unsafe_allow_html=True)
        
        t1, t2 = st.tabs(["Sign In", "Create Account"])
        
        with t1:
            with st.form("login", border=False):
                u = st.text_input("u", placeholder="Username", label_visibility="collapsed")
                p = st.text_input("p", type="password", placeholder="Password", label_visibility="collapsed")
                if st.form_submit_button("Sign In →", type="primary", use_container_width=True):
                    if api.login(u, p): st.rerun()
                        
        with t2:
            with st.form("signup", border=False):
                fn = st.text_input("fn", placeholder="Full Name", label_visibility="collapsed")
                us = st.text_input("us", placeholder="Username", label_visibility="collapsed")
                em = st.text_input("em", placeholder="Email", label_visibility="collapsed")
                pw = st.text_input("pw", type="password", placeholder="Password", label_visibility="collapsed")
                if st.form_submit_button("Create Account", type="primary", use_container_width=True):
                    if api.signup(us, pw, em, fn, "2000-01-01"):
                        if api.login(us, pw): st.rerun()
