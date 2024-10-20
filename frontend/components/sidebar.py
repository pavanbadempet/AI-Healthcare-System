"""
Premium Sidebar Component - AI Healthcare System
=================================================
Clean, modern navigation with polished styling.
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
    
    # Sidebar styling - minimal to not break native toggle
    st.markdown("""
    <style>
    /* Sidebar appearance - NOT blocking collapse */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0F172A 0%, #1E293B 100%) !important;
        border-right: 1px solid rgba(59, 130, 246, 0.15) !important;
    }
    
    section[data-testid="stSidebar"] > div:first-child {
        padding: 1.5rem 1rem !important;
    }
    
    /* Style the toggle buttons nicely */
    button[data-testid="stSidebarCollapseButton"],
    [data-testid="stSidebarCollapsedControl"] button {
        background: linear-gradient(135deg, #3B82F6, #8B5CF6) !important;
        border: none !important;
        border-radius: 8px !important;
        color: white !important;
        box-shadow: 0 2px 10px rgba(59, 130, 246, 0.3) !important;
        transition: all 0.2s ease !important;
    }
    
    button[data-testid="stSidebarCollapseButton"]:hover,
    [data-testid="stSidebarCollapsedControl"] button:hover {
        transform: scale(1.05) !important;
        box-shadow: 0 4px 15px rgba(59, 130, 246, 0.4) !important;
    }
    
    /* Hide default nav */
    div[data-testid="stSidebarNav"] {
        display: none !important;
    }
    
    /* Navigation link styling */
    section[data-testid="stSidebar"] .nav-link {
        transition: all 0.2s ease !important;
        border-left: 3px solid transparent !important;
    }
    
    section[data-testid="stSidebar"] .nav-link:hover {
        background: rgba(59, 130, 246, 0.1) !important;
        border-left: 3px solid #3B82F6 !important;
    }
    
    section[data-testid="stSidebar"] .nav-link-selected {
        border-left: 3px solid #3B82F6 !important;
    }
    
    /* Sign out button */
    section[data-testid="stSidebar"] button[kind="secondary"] {
        background: rgba(239, 68, 68, 0.1) !important;
        border: 1px solid rgba(239, 68, 68, 0.3) !important;
        color: #F87171 !important;
        border-radius: 8px !important;
        transition: all 0.2s ease !important;
    }
    
    section[data-testid="stSidebar"] button[kind="secondary"]:hover {
        background: rgba(239, 68, 68, 0.2) !important;
        transform: translateY(-1px);
    }
    </style>
    """, unsafe_allow_html=True)
    
    with st.sidebar:
        # --- 1. BRAND HEADER ---
        st.markdown("""
        <div style="
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 1rem;
            background: linear-gradient(135deg, rgba(59, 130, 246, 0.1) 0%, rgba(139, 92, 246, 0.05) 100%);
            border-radius: 12px;
            border: 1px solid rgba(59, 130, 246, 0.2);
            margin-bottom: 1.5rem;
        ">
            <div style="font-size: 2rem;">🏥</div>
            <div>
                <div style="
                    font-weight: 700;
                    font-size: 1.1rem;
                    color: white;
                ">AI Healthcare</div>
                <div style="
                    font-size: 0.75rem;
                    color: #64748B;
                ">Powered by AI</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # --- 2. USER QUICK INFO (if logged in) ---
        username = st.session_state.get('username', 'Guest')
        avatar_letter = username[0].upper() if username else 'G'
        
        st.markdown(f"""
        <div style="
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 0.75rem 1rem;
            background: rgba(30, 41, 59, 0.5);
            border-radius: 10px;
            margin-bottom: 1.5rem;
        ">
            <div style="
                width: 40px;
                height: 40px;
                border-radius: 10px;
                background: linear-gradient(135deg, #3B82F6, #8B5CF6);
                display: flex;
                align-items: center;
                justify-content: center;
                color: white;
                font-weight: 700;
                font-size: 1rem;
            ">{avatar_letter}</div>
            <div style="flex: 1; min-width: 0;">
                <div style="
                    color: #F1F5F9;
                    font-size: 0.9rem;
                    font-weight: 600;
                    white-space: nowrap;
                    overflow: hidden;
                    text-overflow: ellipsis;
                ">{username}</div>
                <div style="
                    display: flex;
                    align-items: center;
                    gap: 4px;
                ">
                    <span style="
                        width: 6px;
                        height: 6px;
                        background: #22C55E;
                        border-radius: 50%;
                    "></span>
                    <span style="color: #22C55E; font-size: 0.7rem;">Online</span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # --- 3. NAVIGATION LABEL ---
        st.markdown("""
        <div style="
            font-size: 0.7rem;
            color: #64748B;
            text-transform: uppercase;
            letter-spacing: 0.1em;
            font-weight: 600;
            margin-bottom: 0.5rem;
            padding-left: 0.5rem;
        ">Menu</div>
        """, unsafe_allow_html=True)
        
        # --- 4. MAIN NAVIGATION ---
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
            "speedometer2",      # Dashboard
            "chat-dots",         # Chat
            "droplet",           # Diabetes
            "heart",             # Heart
            "clipboard2-pulse",  # Liver
            "capsule",           # Kidney
            "lungs",             # Lungs
            "person",            # Profile
            "credit-card",       # Pricing
            "camera-video",      # Telemedicine
            "info-circle"        # About
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
            styles={
                "container": {
                    "padding": "0",
                    "background-color": "transparent",
                },
                "icon": {
                    "color": "#64748B",
                    "font-size": "1rem",
                },
                "nav-link": {
                    "font-size": "0.9rem",
                    "text-align": "left",
                    "margin": "3px 0",
                    "padding": "0.65rem 0.75rem",
                    "border-radius": "8px",
                    "color": "#94A3B8",
                    "font-weight": "500",
                    "background": "transparent",
                },
                "nav-link-selected": {
                    "background": "linear-gradient(90deg, rgba(59, 130, 246, 0.2), rgba(59, 130, 246, 0.05))",
                    "color": "#60A5FA",
                    "font-weight": "600",
                },
            }
        )
        
        # --- 5. SPACER + SIGN OUT ---
        st.markdown("<div style='height: 2rem'></div>", unsafe_allow_html=True)
        
        if st.button("🚪 Sign Out", type="secondary", width="stretch", key="logout_btn"):
            api.clear_session()
            st.rerun()
        
        # --- 6. VERSION ---
        st.markdown("""
        <div style="
            text-align: center;
            padding-top: 1.5rem;
            color: #475569;
            font-size: 0.7rem;
        ">
            v2.1 — © 2026 AI Healthcare
        </div>
        """, unsafe_allow_html=True)
    
    return selected
