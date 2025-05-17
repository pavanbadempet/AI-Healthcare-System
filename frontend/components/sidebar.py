"""
Premium Sidebar Component - AI Healthcare System
=================================================
Clean, modern navigation using standard Streamlit components.
"""
import streamlit as st
from streamlit_option_menu import option_menu
from frontend.utils import api, i18n

def render_sidebar():
    """
    Renders a clean, modern sidebar with:
    1. Brand header
    2. Navigation menu
    3. User profile card
    4. Sign out button
    """
    
    # --- SIDEBAR RENDER ---
    with st.sidebar:
        # 1. Logo & Brand
        c1, c2 = st.columns([1, 4])
        with c1:
            try:
                import os
                # Construct absolute path to avoid MediaFileStorageError
                base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                logo_path = os.path.join(base_dir, "frontend", "static", "logo.png")
                
                if os.path.exists(logo_path):
                    st.image(logo_path, width=50)
                else:
                    st.markdown("### 🏥")
            except Exception as e:
                st.markdown("### 🏥")
        with c2:
            st.markdown("### AI Healthcare\n<small style='color: #64748B'>Patient Portal</small>", unsafe_allow_html=True)
            
        st.markdown("---")

        # 2. User Info (Standard Streamlit Container)
        username = st.session_state.get('username', 'Guest')
        if username != 'Guest':
            with st.container():
                # Simple clean profile display
                st.markdown(f"""
                <div style="background-color: rgba(255, 255, 255, 0.05); padding: 10px; border-radius: 8px; display: flex; align-items: center; gap: 10px; margin-bottom: 20px;">
                    <div style="background: #3B82F6; width: 32px; height: 32px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; color: white;">
                        {username[0].upper()}
                    </div>
                    <div>
                        <div style="font-weight: 600; font-size: 14px; color: #F1F5F9;">{username}</div>
                        <div style="font-size: 12px; color: #4ADE80;">● Online</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        
        # 3. Navigation Menu
        nav_options = [
            i18n.get_text("dashboard"),
            i18n.get_text("chat"),
            i18n.get_text("diabetes_pred"),
            i18n.get_text("heart_pred"),
            i18n.get_text("liver_pred"),
            i18n.get_text("kidney_pred"),
            i18n.get_text("lung_pred"),
            i18n.get_text("profile"),
            i18n.get_text("pricing"),
            i18n.get_text("telemedicine"),
            i18n.get_text("about")
        ]
        
        nav_icons = [
            "speedometer2", "chat-dots", "droplet", "heart", 
            "clipboard2-pulse", "capsule", "lungs", "person", 
            "credit-card", "camera-video", "info-circle"
        ]
        
        # Admin option
        if username == "admin" or username.startswith("admin_"):
            nav_options.append(i18n.get_text("admin"))
            nav_icons.append("shield-lock")

        selected = option_menu(
            menu_title=None,
            options=nav_options,
            icons=nav_icons,
            default_index=0,
            key="main_sidebar_nav",
            styles={
                "container": {"background-color": "transparent", "padding": "0"},
                "icon": {"color": "#94A3B8", "font-size": "14px"}, 
                "nav-link": {
                    "font-size": "14px",
                    "text-align": "left",
                    "margin": "0px",
                    "padding": "10px",
                    "color": "#CBD5E1",
                },
                "nav-link-selected": {
                    "background-color": "rgba(59, 130, 246, 0.2)",
                    "color": "#60A5FA",
                    "font-weight": "600",
                    "border-left": "3px solid #3B82F6"
                },
            }
        )
        
        # 4. Footer / Sign Out
        st.markdown("---")
        # Updated: use width='stretch' instead of deprecated use_container_width=True
        if st.button("🚪 Sign Out", key="logout_btn", type="secondary"): 
            api.clear_session()
            st.rerun()
            
        st.markdown("<div style='text-align: center; color: #475569; font-size: 12px; margin-top: 20px;'>v2.1 • © 2026 AI Healthcare</div>", unsafe_allow_html=True)
    
    return selected
