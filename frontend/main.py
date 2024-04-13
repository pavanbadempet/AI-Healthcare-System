"""
AI Healthcare System - Frontend Application
============================================

Main entry point. Orchestrates the UI using the Sidebar Navigation pattern.
Delegates logic to Views and Utilities.

Author: Pavan Badempet
"""
import streamlit as st
import os
import sys

# Add project root to path to allow imports from frontend package
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from streamlit_lottie import st_lottie
import requests
from streamlit_option_menu import option_menu

# --- Import Custom Modules ---
from frontend.utils import api
from frontend.views import (
    auth_view, 
    dashboard_view, 
    profile_view, 
    chat_view, 
    diabetes_view, 
    heart_view, 
    liver_view,
    kidney_view,
    lungs_view
)

# --- Configuration ---
# Get logo path for favicon
import os as _os
_logo_path = _os.path.join(_os.path.dirname(__file__), "static", "logo.png")

st.set_page_config(
    page_title="AI Healthcare System",
    page_icon=_logo_path if _os.path.exists(_logo_path) else "🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CSS Injection ---
def local_css(file_name):
    if os.path.exists(file_name):
        with open(file_name) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    else:
        st.warning(f"Style file not found: {file_name}")

# Adjust path relative to this script
css_path = os.path.join(os.path.dirname(__file__), "static", "style.css")
local_css(css_path)

# --- Animation Loader ---
@st.cache_data
def load_lottieurl(url: str):
    try:
        r = requests.get(url)
        if r.status_code != 200: return None
        return r.json()
    except: return None

from frontend.components import sidebar

# --- Main App Orchestrator ---
def main():
    # 1. Initialize Session
    if 'token' not in st.session_state:
        # Try to load from local file (persistence)
        session = api.load_session()
        if session:
            st.session_state['token'] = session.get('token')
            st.session_state['username'] = session.get('username')

    # 2. Check Auth State
    if 'token' not in st.session_state:
        auth_view.render_auth_page()
        return

    # 3. Sidebar Navigation (DELEGATED TO COMPONENT)
    selected = sidebar.render_sidebar()
    
    # 4. Route to View
    if selected == "Dashboard":
        dashboard_view.render_dashboard()
    elif selected == "AI Chat Assistant":
        chat_view.render_chat_page()
    elif selected == "Diabetes Prediction":
        diabetes_view.render_diabetes_page()
    elif selected == "Heart Disease Prediction":
        heart_view.render_heart_page()
    elif selected == "Liver Disease Prediction":
        liver_view.render_liver_page()
    elif selected == "Kidney Disease Prediction":
        kidney_view.render_kidney_page()
    elif selected == "Lung Cancer Prediction":
        lungs_view.render_lungs_page()
    elif selected == "My Profile":
        profile_view.render_profile_page()
    elif selected == "Plans & Pricing":
        from frontend.views import pricing_view
        pricing_view.render_pricing_page()
    elif selected == "About & Legal":
        from frontend.views import about_view
        about_view.render_about_page()

if __name__ == '__main__':
    main()
