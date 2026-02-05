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
        
        # Use Image if available, else fallback to SVG or Emoji
        if img_b64:
            logo_html = f'<img src="data:image/png;base64,{img_b64}" style="width: 42px; height: 42px; object-fit: contain;">'
        else:
            logo_html = "🏥"

        st.markdown(f"""
<div style="display: flex; align-items: center; gap: 12px; padding: 15px 0 25px 0;">
    {logo_html}
    <div style="line-height: 1.2;">
        <div style="font-size: 22px; font-weight: 700; color: #F8FAFC; letter-spacing: -0.5px;">AI Healthcare</div>
        <div style="font-size: 13px; color: #94A3B8; font-weight: 400;">Patient Portal</div>
    </div>
</div>""".replace('\n', ''), unsafe_allow_html=True)
            
        st.markdown('<div style="height: 1px; background: rgba(255,255,255,0.1); margin-bottom: 20px;"></div>', unsafe_allow_html=True)

        # 2. User Info (Standard Streamlit Container)
        username = st.session_state.get('username', 'Guest')
        if username != 'Guest':
            with st.container():
                # Simple clean profile display
                # Simple clean profile display with Dynamic Picture
                pic = st.session_state.get('profile_picture')
                
                # Flattened HTML to prevent Markdown code block bugs
                if pic:
                    avatar_html = (
                        f'<div style="width: 38px; height: 38px; border-radius: 50%; overflow: hidden; border: 2px solid #3B82F6;">'
                        f'<img src="{pic}" style="width: 100%; height: 100%; object-fit: cover;">'
                        f'</div>'
                    )
                else:
                    avatar_html = (
                        f'<div style="background: #3B82F6; width: 32px; height: 32px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; color: white;">'
                        f'{username[0].upper()}'
                        f'</div>'
                    )

                st.markdown(f"""
<div style="background-color: rgba(255, 255, 255, 0.05); padding: 10px; border-radius: 8px; display: flex; align-items: center; gap: 10px; margin-bottom: 20px;">
    {avatar_html}
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
        # Strict Check: Only show if role is explicitly 'admin'
        user_role = st.session_state.get('role', 'patient')
        if user_role == 'admin':
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
