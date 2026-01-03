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
    
    # --- CENTERED LAYOUT ---
    # Use 3 columns to center the content
    c1, c2, c3 = st.columns([1, 1.4, 1])
    
    with c2:
        # 1. Centered Header
        st.markdown("""
        <div style="text-align: center; margin-bottom: 2rem; animation: fadeInUp 0.8s ease-out;">
            <div style="font-size: 3.5rem; margin-bottom: 0.5rem; filter: drop-shadow(0 0 20px rgba(59, 130, 246, 0.4));">🏥</div>
            <h1 style="
                font-family: 'Outfit', sans-serif;
                font-size: 2.5rem; 
                font-weight: 800; 
                margin: 0;
                background: linear-gradient(135deg, #FFFFFF 0%, #94A3B8 100%);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                letter-spacing: -1px;
            ">AI Healthcare</h1>
            <p style="
                background: linear-gradient(90deg, #60A5FA, #34D399); 
                -webkit-background-clip: text; 
                -webkit-text-fill-color: transparent;
                font-size: 1.1rem; 
                font-weight: 600; 
                margin-top: 0.5rem;
                letter-spacing: 1px;
            ">
                PREDICT. PREVENT. PROTECT.
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # 2. Glass Card Container for Auth
        st.markdown('<div class="auth-container">', unsafe_allow_html=True)
        
        # Auth Tabs
        auth_tabs = st.tabs(["🔐 Login", "📝 Create Account"])
        
        # ========== LOGIN TAB ==========
        with auth_tabs[0]:
            st.markdown("<br>", unsafe_allow_html=True)
            with st.form("login_form", border=False):
                username = st.text_input("Username", placeholder="Enter your username")
                password = st.text_input("Password", type="password", placeholder="••••••••")
                
                st.markdown("<br>", unsafe_allow_html=True)
                
                # Full width button
                submitted = st.form_submit_button("Sign In", type="primary", use_container_width=True)
                
                if submitted:
                    if not username or not password:
                        st.warning("Please enter credentials.")
                    else:
                        with st.spinner("Authenticating..."):
                            if api.login(username, password):
                                st.rerun()
                            else:
                                st.error("Invalid username or password.")

        # ========== SIGNUP TAB ==========
        with auth_tabs[1]:
            st.markdown("<br>", unsafe_allow_html=True)
            with st.form("signup_form", border=False):
                col_a, col_b = st.columns(2)
                with col_a:
                    new_fullname = st.text_input("Full Name", placeholder="John Doe")
                with col_b:
                    new_user = st.text_input("Username", placeholder="johndoe")
                
                new_email = st.text_input("Email", placeholder="john@email.com")
                new_pass = st.text_input("Password", type="password", placeholder="••••••••")
                new_dob = st.date_input("Date of Birth", value=pd.to_datetime("2000-01-01"))
                
                st.markdown("<br>", unsafe_allow_html=True)
                agree = st.checkbox("I agree to Terms of Service & Medical Disclaimer")
                
                submitted_up = st.form_submit_button("Create Account", type="primary", use_container_width=True)
                
                if submitted_up:
                    if not agree:
                        st.error("You must agree to the terms.")
                    elif not new_user or not new_pass or not new_email:
                        st.warning("Please fill all required fields.")
                    else:
                        with st.spinner("Creating secure account..."):
                            if api.signup(new_user, new_pass, new_email, new_fullname, new_dob):
                                st.success("Account Created! Signing in...")
                                if api.login(new_user, new_pass):
                                    st.rerun()
                                else:
                                    st.info("Please login manually.")
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Footer
        st.markdown("""
        <div style="text-align: center; margin-top: 2rem; color: #64748B; font-size: 0.8rem;">
            Secure Encrypted Connection • HIPAA Compliant • Powered by Advanced AI
        </div>
        """, unsafe_allow_html=True)
