import streamlit as st
from streamlit_option_menu import option_menu
from frontend.utils import api

def render_sidebar():
    """
    Renders the Premium Sidebar with:
    1. Brand Header (Top)
    2. Navigation (Middle)
    3. User Profile Card (Bottom)
    """
    with st.sidebar:
        # --- 1. BRAND HEADER ---
        st.markdown(
            """
            <div style="margin-bottom: 20px; padding-top: 10px;">
                <h2 style="
                    margin: 0; 
                    font-family: 'Outfit', sans-serif; 
                    font-weight: 700; 
                    font-size: 1.5rem;
                    background: linear-gradient(90deg, #3B82F6, #8B5CF6); 
                    -webkit-background-clip: text; 
                    -webkit-text-fill-color: transparent;
                ">
                    AI Healthcare
                </h2>
                <div style="
                    font-size: 0.75rem; 
                    color: #64748B; 
                    letter-spacing: 0.05em; 
                    text-transform: uppercase; 
                    font-weight: 600; 
                    margin-top: 4px;
                ">
                    System v2.0
                </div>
            </div>
            """, 
            unsafe_allow_html=True
        )

        # --- 2. NAVIGATION ---
        selected = option_menu(
            menu_title=None, 
            options=[
                "Dashboard", 
                "AI Chat Assistant", 
                "Diabetes Prediction", 
                "Heart Disease Prediction", 
                "Liver Disease Prediction", 
                "Kidney Disease Prediction",
                "Lung Cancer Prediction",
                "My Profile"
            ],
            icons=[
                "speedometer2", 
                "robot", 
                "droplet-half", 
                "heart-pulse", 
                "activity", 
                "capsule", 
                "wind", 
                "person-circle"
            ],
            default_index=0,
            styles={
                "container": {
                    "padding": "0!important", 
                    "background-color": "transparent",
                    "margin": "0"
                },
                "icon": {
                    "color": "#94A3B8", 
                    "font-size": "1.1rem"
                }, 
                "nav-link": {
                    "font-family": "'Inter', sans-serif",
                    "font-size": "0.95rem",
                    "text-align": "left", 
                    "margin": "0px",
                    "padding": "10px 15px",
                    "border-radius": "8px",
                    "color": "#CBD5E1",
                    "font-weight": "400",
                },
                "nav-link-selected": {
                    "background-color": "rgba(59, 130, 246, 0.1)",
                    "color": "#60A5FA",
                    "font-weight": "600",
                    "border-left": "3px solid #60A5FA",
                },
            }
        )

        # --- 3. SPACER (Pushes profile to bottom if needed, though Streamlit layout is top-down) ---
        st.markdown("<div style='height: 50px;'></div>", unsafe_allow_html=True)
        
        # --- 4. USER PROFILE CARD (Footer) ---
        username = st.session_state.get('username', 'Guest')
        st.markdown(
            f"""
            <div style="
                background: rgba(30, 41, 59, 0.4); 
                border: 1px solid rgba(255, 255, 255, 0.05);
                border-radius: 12px; 
                padding: 12px; 
                display: flex; 
                align-items: center; 
                gap: 12px;
                margin-top: auto; 
            ">
                <div style="
                    width: 36px; 
                    height: 36px; 
                    border-radius: 50%; 
                    background: linear-gradient(135deg, #3B82F6, #2563EB); 
                    display: flex; 
                    align-items: center; 
                    justify_content: center;
                    color: white;
                    font-weight: 700;
                    font-size: 1rem;
                ">
                    {username[0].upper() if username else 'G'}
                </div>
                <div style="flex-grow: 1;">
                    <div style="color: #E2E8F0; font-size: 0.9rem; font-weight: 500;">{username}</div>
                    <div style="color: #64748B; font-size: 0.75rem;">Premium Plan</div>
                </div>
            </div>
            """, 
            unsafe_allow_html=True
        )
        
        # Logout Button (Subtle, Text only)
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Sign Out", type="secondary", use_container_width=True):
            api.clear_session()
            st.rerun()

    return selected
