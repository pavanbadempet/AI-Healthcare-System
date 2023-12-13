import streamlit as st
from frontend.utils import api

def render_auth_page():
    st.markdown("<h1 style='text-align: center; color: #4A90E2;'>AIO Healthcare System</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center;'>AI-Powered Disease Prediction & Health Assistance</p>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        tab1, tab2 = st.tabs(["Login", "Sign Up"])
        
        with tab1:
            with st.form("login_form"):
                username = st.text_input("Username")
                password = st.text_input("Password", type="password")
                submitted = st.form_submit_button("Login", use_container_width=True)
                if submitted:
                    if api.login(username, password):
                        st.success("Login Successful!")
                        st.rerun()

        with tab2:
            st.markdown("### Create New Account")
            with st.form("signup_form"):
                new_user = st.text_input("Username")
                new_pass = st.text_input("Password", type="password", help="Must be 8+ chars, letters & numbers")
                new_email = st.text_input("Email")
                full_name = st.text_input("Full Name")
                dob = st.date_input("Date of Birth")
                
                submitted = st.form_submit_button("Sign Up", use_container_width=True)
                if submitted:
                    if api.signup(new_user, new_pass, new_email, full_name, dob):
                        st.success("Account Created! Swapping to Login...")
