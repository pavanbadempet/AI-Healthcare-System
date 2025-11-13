"""
Auth View - Balanced Design
===========================
Fits in viewport with proper sizing - not too cramped.
"""
import streamlit as st
from frontend.utils import api

def render_auth_page():
    """Auth page with balanced design."""
    
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
    padding: 2rem 2rem !important;
    height: 100vh !important;
    overflow: hidden !important;
}

[data-testid="stHorizontalBlock"] {
    height: calc(100vh - 4rem) !important;
    align-items: center !important;
}

/* Form styling - proper sizing */
div.stForm {
    padding: 1.25rem !important;
    border-radius: 16px !important;
    background: rgba(15, 23, 42, 0.6) !important;
    border: 1px solid rgba(255,255,255,0.08) !important;
}

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
    background: transparent !important;
    border-bottom: 1px solid rgba(255,255,255,0.1) !important;
    margin-bottom: 1rem !important;
}

.stTabs [data-baseweb="tab"] {
    padding: 0.5rem 1rem !important;
    font-size: 0.9rem !important;
}

.stTabs [aria-selected="true"] {
    color: #60A5FA !important;
    border-bottom: 2px solid #60A5FA !important;
}

/* Input styling */
div[data-testid="stTextInput"],
div[data-testid="stPasswordInput"] {
    margin-bottom: 0.75rem !important;
}

div[data-testid="stTextInput"] input,
div[data-testid="stPasswordInput"] input {
    padding: 0.6rem 0.8rem !important;
    font-size: 0.95rem !important;
    border-radius: 10px !important;
}

div[data-testid="stFormSubmitButton"] button {
    padding: 0.65rem 1rem !important;
    font-size: 0.95rem !important;
    border-radius: 10px !important;
    margin-top: 0.5rem !important;
    background: linear-gradient(135deg, #10B981 0%, #059669 100%) !important;
    border: none !important;
    color: white !important;
    font-weight: 600 !important;
    cursor: pointer !important;
    transition: all 0.2s ease !important;
    box-shadow: 0 4px 12px rgba(16, 185, 129, 0.3) !important;
}

div[data-testid="stFormSubmitButton"] button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 6px 20px rgba(16, 185, 129, 0.4) !important;
    background: linear-gradient(135deg, #34D399 0%, #10B981 100%) !important;
}

div[data-testid="stFormSubmitButton"] button:active {
    transform: translateY(0) !important;
    box-shadow: 0 2px 8px rgba(16, 185, 129, 0.3) !important;
}
</style>
""", unsafe_allow_html=True)

    # Logo Import & Encoding
    import base64
    import os
    
    def get_img_as_base64(file_path):
        try:
            with open(file_path, "rb") as f:
                data = f.read()
            return base64.b64encode(data).decode()
        except: return None

    logo_path = os.path.join(os.path.dirname(__file__), "..", "static", "logo.png")
    img_b64 = get_img_as_base64(logo_path)
    
    if img_b64:
        logo_html = f'<img src="data:image/png;base64,{img_b64}" style="width: 80px; height: 80px; object-fit: contain; filter: drop-shadow(0 0 10px rgba(59,130,246,0.5));">'
    else:
        logo_html = '<div style="font-size: 60px;">🏥</div>'
    
    col1, col2 = st.columns([1.2, 1])
    
    # Left - Branding
    with col1:
        st.markdown(f"""
<div style="padding: 2rem;">
    <div style="margin-bottom: 1rem;">
        {logo_html}
    </div>
    <h1 style="font-size: 2.75rem; margin: 0 0 0.75rem 0; color: white; line-height: 1.15; font-weight: 800;">
        The Future of<br>
        <span style="background: linear-gradient(90deg, #60A5FA, #34D399); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">AI Healthcare</span>
    </h1>
    <p style="font-size: 1.1rem; color: #94A3B8; margin: 0 0 1.5rem 0; line-height: 1.5; max-width: 450px;">
        Hospital-grade predictive diagnostics. Secure data protection. Real-time analysis powered by AI.
    </p>
    <div style="display: flex; gap: 0.75rem;">
        <div style="background: rgba(255,255,255,0.03); padding: 0.75rem 1rem; border-radius: 12px; border: 1px solid rgba(255,255,255,0.08); text-align: center;">
            <div style="font-size: 1.1rem; font-weight: 700; color: #F8FAFC;">99.8%</div>
            <div style="font-size: 0.75rem; color: #64748B;">Precision</div>
        </div>
        <div style="background: rgba(255,255,255,0.03); padding: 0.75rem 1rem; border-radius: 12px; border: 1px solid rgba(255,255,255,0.08); text-align: center;">
            <div style="font-size: 1.1rem; font-weight: 700; color: #F8FAFC;">Encrypted</div>
            <div style="font-size: 0.75rem; color: #64748B;">Data</div>
        </div>
        <div style="background: rgba(255,255,255,0.03); padding: 0.75rem 1rem; border-radius: 12px; border: 1px solid rgba(255,255,255,0.08); text-align: center;">
            <div style="font-size: 1.1rem; font-weight: 700; color: #F8FAFC;">Global</div>
            <div style="font-size: 0.75rem; color: #64748B;">Access</div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

    # Right - Auth Form
    with col2:
        st.markdown("""
<div style="text-align: center; margin-bottom: 1rem;">
    <h2 style="font-size: 1.75rem; margin: 0; color: white; font-weight: 600;">Patient & Staff Portal</h2>
    <p style="font-size: 0.95rem; color: #94A3B8; margin: 0.5rem 0 0 0;">Secure Login for Patients & Clinicians</p>
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
            with st.form("signup", border=False):
                us = st.text_input("Username", placeholder="Choose a username", label_visibility="collapsed")
                em = st.text_input("Email", placeholder="Your email", label_visibility="collapsed")
                pw = st.text_input("Password", type="password", placeholder="Create password", label_visibility="collapsed")
                if st.form_submit_button("Register", type="primary", width="stretch"):
                    if api.signup(us, pw, em, us, "2000-01-01"):
                        if api.login(us, pw): st.rerun()
        
        st.markdown('<p style="text-align: center; font-size: 0.8rem; color: #475569; margin-top: 1rem;">Powered by Advanced AI</p>', unsafe_allow_html=True)
