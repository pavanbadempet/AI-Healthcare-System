"""
Auth View - Premium Login/Signup Experience
============================================
Compact, no-scroll design with auto-login after signup.
"""
import streamlit as st
import pandas as pd
from frontend.utils import api


def render_auth_page():
    """Render a compact, premium auth experience."""
    
    # Custom CSS for compact form
    st.markdown("""
    <style>
    /* Compact form fields */
    .stTextInput > div > div > input {
        padding: 0.6rem 0.8rem !important;
    }
    .stDateInput > div > div > input {
        padding: 0.6rem 0.8rem !important;
    }
    /* Tighter spacing */
    .stForm > div {
        gap: 0.5rem !important;
    }
    /* Smaller labels */
    .stTextInput label, .stDateInput label {
        font-size: 0.85rem !important;
        margin-bottom: 0.2rem !important;
    }
    
    /* Animations */
    @keyframes fadeInUp {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }
    .hero-animate {
        animation: fadeInUp 0.8s ease-out forwards;
    }
    .hero-delay-1 { animation-delay: 0.2s; opacity: 0; }
    .hero-delay-2 { animation-delay: 0.4s; opacity: 0; }
    </style>
    """, unsafe_allow_html=True)
    
    # --- COMPACT CENTERED LAYOUT (NO SCROLL) ---
    st.markdown("""
    <style>
    /* Force Remove Streamlit Vertical Padding */
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 0rem !important;
        max-width: 100% !important;
    }
    /* Compact Header */
    .auth-header {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 1rem;
        margin-bottom: 1rem;
    }
    </style>
    """, unsafe_allow_html=True)

    # Use 3 columns to center
    c1, c2, c3 = st.columns([1, 1.2, 1]) # Slightly narrower middle
    
    with c2:
        # Glass Card Start
        st.markdown('<div class="auth-container" style="padding: 1.5rem;">', unsafe_allow_html=True)
        
        # 1. Header INSIDE Card (Horizontal)
        st.markdown("""
        <div class="auth-header">
            <div style="font-size: 2.5rem; filter: drop-shadow(0 0 10px rgba(59,130,246,0.5));">🏥</div>
            <div>
                <h1 style="
                    font-size: 1.8rem; 
                    margin: 0; 
                    line-height: 1;
                    background: linear-gradient(135deg, #FFF 0%, #CBD5E1 100%);
                    -webkit-background-clip: text;
                    -webkit-text-fill-color: transparent;
                ">AI Healthcare</h1>
                <div style="font-size: 0.7rem; color: #60A5FA; letter-spacing: 2px; margin-top: 4px;">PREDICT. PREVENT.</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Auth Tabs
        auth_tabs = st.tabs(["🔐 Login", "📝 Sign Up"])
        
        # ========== LOGIN TAB ==========
        with auth_tabs[0]:
            st.markdown("<div style='margin-top: 1rem;'></div>", unsafe_allow_html=True)
            with st.form("login_form", border=False):
                username = st.text_input("Username", placeholder="Username", label_visibility="collapsed")
                password = st.text_input("Password", type="password", placeholder="Password", label_visibility="collapsed")
                
                st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
                submitted = st.form_submit_button("Sign In →", type="primary", use_container_width=True)
                
                if submitted:
                    if username and password:
                         with st.spinner(""):
                            if api.login(username, password): st.rerun()
                    else:
                        st.warning("Required fields missing")

        # ========== SIGNUP TAB ==========
        with auth_tabs[1]:
             st.markdown("<div style='margin-top: 0.5rem;'></div>", unsafe_allow_html=True)
             with st.form("signup_form", border=False):
                c_a, c_b = st.columns(2)
                with c_a: new_fullname = st.text_input("Full Name", placeholder="John Doe", label_visibility="collapsed")
                with c_b: new_email = st.text_input("Email", placeholder="john@email.com", label_visibility="collapsed")
                
                c_c, c_d = st.columns(2)
                with c_c: new_user = st.text_input("User", placeholder="Username", label_visibility="collapsed")
                with c_d: new_pass = st.text_input("Pass", type="password", placeholder="••••••", label_visibility="collapsed")
                
                new_dob = st.date_input("DOB", value=pd.to_datetime("2000-01-01"), label_visibility="collapsed")
                agree = st.checkbox("Agree to Terms", value=False)
                
                if st.form_submit_button("Create Account", type="primary", use_container_width=True):
                    if api.signup(new_user, new_pass, new_email, new_fullname, new_dob):
                         if api.login(new_user, new_pass): st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)

