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
    
    # SPLIT LAYOUT: Hero | Auth Form
    hero_col, auth_col = st.columns([1.2, 1], gap="large")
    
    with hero_col:
        # Get logo path
        import os
        logo_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static", "logo.png")
        
        st.markdown('<div style="padding-top: 30px; padding-right: 20px; border-right: 1px solid #1e293b;">', unsafe_allow_html=True)
        
        # Logo + Brand name row
        logo_col, brand_col = st.columns([0.15, 0.85])
        with logo_col:
            if os.path.exists(logo_path):
                st.image(logo_path, width=52)
            else:
                st.markdown('<div style="font-size:2rem;">🏥</div>', unsafe_allow_html=True)
        with brand_col:
            st.markdown("""
            <div style="
                font-family: 'Outfit', sans-serif;
                font-weight: 700;
                font-size: 1.4rem;
                background: linear-gradient(90deg, #FFFFFF 0%, #94A3B8 100%);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                margin-top: 8px;
            ">AI Healthcare</div>
            <div style="font-size: 0.7rem; color: #64748B; letter-spacing: 0.08em; text-transform: uppercase;">
                ⚡ Powered by ML
            </div>
            """, unsafe_allow_html=True)
        
        # Tagline
        st.markdown("""
<div class="hero-animate">
<h1 style="font-size: 2.3rem; font-weight: 800; background: linear-gradient(135deg, #60A5FA, #34D399); -webkit-background-clip: text; -webkit-text-fill-color: transparent; line-height: 1.2; margin: 1rem 0;">Predict. Prevent.<br>Protect.</h1>
</div>
<p class="hero-animate hero-delay-1" style="font-size: 0.9rem; color: #94A3B8; line-height: 1.6; margin-bottom: 1rem;">Advanced disease prediction using machine learning.</p>
<div class="hero-animate hero-delay-2" style="display: flex; flex-wrap: wrap; gap: 8px;">
<span style="background: rgba(59,130,246,0.1); padding: 5px 12px; border-radius: 16px; color: #60A5FA; font-size: 0.7rem; border: 1px solid rgba(59,130,246,0.2);">🔒 Secure</span>
<span style="background: rgba(16,185,129,0.1); padding: 5px 12px; border-radius: 16px; color: #34D399; font-size: 0.7rem; border: 1px solid rgba(16,185,129,0.2);">⚡ Real-time</span>
<span style="background: rgba(139,92,246,0.1); padding: 5px 12px; border-radius: 16px; color: #A78BFA; font-size: 0.7rem; border: 1px solid rgba(139,92,246,0.2);">🤖 AI</span>
</div>
</div>
""", unsafe_allow_html=True)


    with auth_col:
        # Tab selection
        auth_tabs = st.tabs(["🔐 Login", "📝 Sign Up"])
        
        # ========== LOGIN TAB ==========
        with auth_tabs[0]:
            st.markdown("##### Welcome Back")
            with st.form("login_form", border=False):
                username = st.text_input("Username", placeholder="your_username", label_visibility="collapsed")
                password = st.text_input("Password", type="password", placeholder="••••••••", label_visibility="collapsed")
                
                col1, col2 = st.columns([1, 1])
                with col2:
                    submit = st.form_submit_button("Login →", type="primary", use_container_width=True)
                
                if submit:
                    if username and password:
                        with st.spinner(""):
                            if api.login(username, password):
                                st.rerun()
                    else:
                        st.warning("Enter username and password")
        
        # ========== SIGNUP TAB ==========
        with auth_tabs[1]:
            st.markdown("##### Create Account")
            with st.form("signup_form", border=False):
                # Row 1: Name + Email (side by side)
                c1, c2 = st.columns(2)
                with c1:
                    new_fullname = st.text_input("Full Name", placeholder="John Doe", key="fname")
                with c2:
                    new_email = st.text_input("Email", placeholder="john@email.com", key="email")
                
                # Row 2: Username + Password (side by side)
                c3, c4 = st.columns(2)
                with c3:
                    new_user = st.text_input("Username", placeholder="johndoe", key="uname")
                with c4:
                    new_pass = st.text_input("Password", type="password", placeholder="••••••••", key="pwd")
                
                # Row 3: DOB (compact)
                new_dob = st.date_input(
                    "Date of Birth", 
                    value=None, 
                    min_value=pd.to_datetime("1900-01-01"), 
                    max_value=pd.to_datetime("today"),
                    format="YYYY-MM-DD"
                )
                
                # Checkbox + Submit (same row)
                terms_agreed = st.checkbox("I agree to Terms & Medical Disclaimer", value=False)
                
                if st.form_submit_button("Create Account →", type="primary", use_container_width=True):
                    # Validation
                    errors = []
                    if not new_fullname: errors.append("Full Name")
                    if not new_email: errors.append("Email")
                    if not new_user: errors.append("Username")
                    if not new_pass: errors.append("Password")
                    if not new_dob: errors.append("Date of Birth")
                    
                    if not terms_agreed:
                        st.error("Please agree to Terms & Disclaimer")
                    elif errors:
                        st.warning(f"Missing: {', '.join(errors)}")
                    else:
                        with st.spinner("Creating account..."):
                            if api.signup(new_user, new_pass, new_email, new_fullname, new_dob):
                                st.success("✅ Account created!")
                                # AUTO-LOGIN after successful signup
                                if api.login(new_user, new_pass):
                                    st.rerun()
                                else:
                                    st.info("Please login with your new credentials.")
