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
    
    # --- SIDEBAR CONTROLLER (Python Fallback) ---
    # If native toggle fails, this button in the MAIN area allows forcing sidebar open
    
    # Initialize state
    if 'sidebar_force_open' not in st.session_state:
        st.session_state.sidebar_force_open = False

    # Logic to handle toggle
    def toggle_sidebar():
        st.session_state.sidebar_force_open = not st.session_state.sidebar_force_open

    # Render a subtle floating toggle button in main area
    placeholder = st.container()
    col1, col2 = placeholder.columns([1, 20])
    with col1:
        if not st.session_state.sidebar_force_open:
            # Styled ghost button for "Show" - Ultra Minimal
            st.markdown("""
            <style>
            div[data-testid="stButton"] button[kind="secondary"] {
                background: transparent !important;
                border: none !important;
                color: #94A3B8 !important;
                padding: 0 !important;
                font-size: 1.5rem !important;
                line-height: 1 !important;
                min-height: 0px !important;
                height: 40px !important;
                width: 40px !important;
                margin-top: -15px !important; /* Pull up to align with where native toggle would be */
                margin-left: -5px !important;
            }
            div[data-testid="stButton"] button[kind="secondary"]:hover {
                background: rgba(59, 130, 246, 0.1) !important;
                color: #3B82F6 !important;
                border-radius: 50% !important;
            }
            /* Hide the container padding to make it flush */
            div[data-testid="stVerticalBlock"] > div:has(div[data-testid="stButton"]) {
                gap: 0 !important;
            }
            </style>
            """, unsafe_allow_html=True)
            st.button("☰", key="custom_sidebar_show", on_click=toggle_sidebar, help="Open Menu")
    
    # If forced open, inject CSS to override collapse
    if st.session_state.sidebar_force_open:
        st.markdown("""
        <style>
            section[data-testid="stSidebar"] {
                transform: translateX(0) !important;
                visibility: visible !important;
                width: 350px !important; /* Wider menu as requested */
                min-width: 350px !important;
            }
            
            /* Hide ONLY the native toggle button safely */
            button[data-testid="stSidebarCollapseButton"],
            [data-testid="stSidebarCollapsedControl"],
            section[data-testid="stSidebar"] button[kind="header"] {
                display: none !important;
                visibility: hidden !important;
            }
        </style>
        """, unsafe_allow_html=True)
        
        # Show a standard "Close Menu" button at the very top of sidebar
        with st.sidebar:
            # Spacer to push button down slightly from the very top edge
            st.markdown("<div style='margin-top: 0.5rem;'></div>", unsafe_allow_html=True)
            if st.button("✖ Close Menu", key="custom_sidebar_close", type="primary", use_container_width=True):
                toggle_sidebar()
                st.rerun()
            st.markdown("<div style='margin-bottom: 1rem;'></div>", unsafe_allow_html=True)

    # --- SIDEBAR RENDER ---
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
