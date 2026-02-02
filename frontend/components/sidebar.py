"""
Premium Sidebar Component - AI Healthcare System
=================================================
Modern glassmorphism-inspired navigation matching the main content aesthetic.
"""
import streamlit as st
from streamlit_option_menu import option_menu
from frontend.utils import api, i18n


def render_sidebar():
    """
    Renders a premium, modern sidebar with:
    1. Glassmorphism brand header with pulse animation
    2. Grouped navigation sections
    3. Premium user profile card with gradient avatar
    """
    
    # Inject custom CSS for sidebar overhaul
    st.markdown("""
    <style>
    /* --- SIDEBAR COMPLETE OVERHAUL --- */
    
    /* Sidebar Container - Glassmorphism Base */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0a0f1a 0%, #0d1321 50%, #111827 100%) !important;
        border-right: 1px solid rgba(59, 130, 246, 0.1) !important;
    }
    
    section[data-testid="stSidebar"]::before {
        content: "";
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: radial-gradient(ellipse at top, rgba(59, 130, 246, 0.05) 0%, transparent 60%);
        pointer-events: none;
    }
    
    section[data-testid="stSidebar"] > div:first-child {
        padding: 1rem 0.75rem !important;
        background: transparent !important;
    }
    
    /* Hide default streamlit nav */
    div[data-testid="stSidebarNav"] {
        display: none !important;
    }
    
    /* Option Menu Styling Override */
    section[data-testid="stSidebar"] .nav-link {
        transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1) !important;
        position: relative;
        overflow: hidden;
    }
    
    section[data-testid="stSidebar"] .nav-link:hover {
        background: linear-gradient(90deg, rgba(59, 130, 246, 0.15), transparent) !important;
        transform: translateX(4px);
    }
    
    section[data-testid="stSidebar"] .nav-link::before {
        content: "";
        position: absolute;
        left: 0;
        top: 50%;
        transform: translateY(-50%);
        width: 3px;
        height: 0;
        background: linear-gradient(180deg, #3B82F6, #8B5CF6);
        border-radius: 0 3px 3px 0;
        transition: height 0.2s ease;
    }
    
    section[data-testid="stSidebar"] .nav-link:hover::before {
        height: 60%;
    }
    
    section[data-testid="stSidebar"] .nav-link-selected::before {
        height: 100% !important;
    }
    
    /* Sidebar button styling */
    section[data-testid="stSidebar"] button[kind="secondary"] {
        background: rgba(239, 68, 68, 0.1) !important;
        border: 1px solid rgba(239, 68, 68, 0.2) !important;
        color: #f87171 !important;
        border-radius: 10px !important;
        transition: all 0.2s ease !important;
    }
    
    section[data-testid="stSidebar"] button[kind="secondary"]:hover {
        background: rgba(239, 68, 68, 0.2) !important;
        border-color: rgba(239, 68, 68, 0.4) !important;
        transform: translateY(-1px);
    }
    
    /* Divider styling */
    section[data-testid="stSidebar"] hr {
        border: none;
        height: 1px;
        background: linear-gradient(90deg, transparent, rgba(148, 163, 184, 0.2), transparent);
        margin: 0.5rem 0;
    }
    </style>
    """, unsafe_allow_html=True)
    
    with st.sidebar:
        # --- 0. LANGUAGE SELECTOR (REMOVED) ---
        # i18n.render_language_selector()
        
        # --- 1. PREMIUM BRAND HEADER WITH LOGO ---
        import os
        logo_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static", "logo.png")
        
        # Brand container
        st.markdown("""
        <div style="
            padding: 1rem;
            margin-bottom: 0.5rem;
            background: linear-gradient(135deg, rgba(59, 130, 246, 0.1) 0%, rgba(139, 92, 246, 0.05) 100%);
            border-radius: 16px;
            border: 1px solid rgba(59, 130, 246, 0.15);
        ">
        """, unsafe_allow_html=True)
        
        # Logo + Text layout
        logo_col, text_col = st.columns([0.25, 0.75])
        with logo_col:
            if os.path.exists(logo_path):
                st.image(logo_path, width=42)
            else:
                st.markdown('<div style="font-size:1.5rem;">🏥</div>', unsafe_allow_html=True)
        with text_col:
            st.markdown("""
            <div style="
                font-family: 'Outfit', sans-serif;
                font-weight: 700;
                font-size: 1.1rem;
                background: linear-gradient(90deg, #FFFFFF 0%, #94A3B8 100%);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                margin-top: 4px;
            ">AI Healthcare System</div>
            """, unsafe_allow_html=True)
        
        st.markdown("</div>", unsafe_allow_html=True)
        
        # --- 2. QUICK STATS MINI CARD ---
        profile = api.fetch_profile()
        if profile and profile.get('user'):
            user_data = profile['user']
            st.markdown(f"""
            <style>
            .sidebar-stats {{
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 8px;
                padding: 0.75rem;
                background: rgba(15, 23, 42, 0.6);
                border-radius: 12px;
                border: 1px solid rgba(148, 163, 184, 0.08);
                margin-bottom: 1rem;
            }}
            .sidebar-stat-item {{
                text-align: center;
                padding: 8px;
            }}
            .sidebar-stat-value {{
                font-size: 1.1rem;
                font-weight: 700;
            }}
            .sidebar-stat-label {{
                font-size: 0.65rem;
                color: #64748B;
                text-transform: uppercase;
            }}
            </style>
            <div class="sidebar-stats">
                <div class="sidebar-stat-item">
                    <div class="sidebar-stat-value" style="color: #60A5FA;">
                        {user_data.get('height', '—')}
                    </div>
                    <div class="sidebar-stat-label">Height cm</div>
                </div>
                <div class="sidebar-stat-item">
                    <div class="sidebar-stat-value" style="color: #34D399;">
                        {user_data.get('weight', '—')}
                    </div>
                    <div class="sidebar-stat-label">Weight kg</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        # --- 3. NAVIGATION SECTION LABEL ---
        st.markdown("""
        <div style="
            font-size: 0.7rem;
            color: #475569;
            text-transform: uppercase;
            letter-spacing: 0.1em;
            font-weight: 600;
            padding: 0 0.5rem;
            margin-bottom: 0.5rem;
        ">Navigation</div>
        """, unsafe_allow_html=True)
        
        # --- 4. MAIN NAVIGATION ---
        # Re-defining options list dynamically with Translations
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
            "grid-1x2-fill",
            "chat-dots-fill",
            "droplet-half",
            "heart-pulse-fill",
            "activity",
            "capsule-pill",
            "lungs-fill",
            "person-badge-fill",
            "credit-card-2-front-fill",
            "camera-video-fill",
            "info-circle-fill"
        ]
        
        # Only show Admin Panel to admins
        username = st.session_state.get('username', '')
        if username == "admin" or username.startswith("admin_"):
            nav_options.append(i18n.get_text("admin"))
            nav_icons.append("shield-lock-fill")

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
                    "font-family": "'Inter', sans-serif",
                    "font-size": "0.875rem",
                    "text-align": "left",
                    "margin": "2px 0",
                    "padding": "0.7rem 0.875rem",
                    "border-radius": "10px",
                    "color": "#94A3B8",
                    "font-weight": "500",
                    "background": "transparent",
                },
                "nav-link-selected": {
                    "background": "linear-gradient(90deg, rgba(59, 130, 246, 0.15), rgba(59, 130, 246, 0.05))",
                    "color": "#60A5FA",
                    "font-weight": "600",
                },
            }
        )
        
        # --- 5. DIVIDER ---
        st.markdown("<hr style='margin: 1rem 0;'>", unsafe_allow_html=True)
        
        # --- 6. PREMIUM USER PROFILE CARD ---
        username = st.session_state.get('username', 'Guest')
        avatar_letter = username[0].upper() if username else 'G'
        
        st.markdown(f"""
        <div style="
            background: linear-gradient(135deg, rgba(30, 41, 59, 0.8) 0%, rgba(15, 23, 42, 0.9) 100%);
            border: 1px solid rgba(148, 163, 184, 0.1);
            border-radius: 14px;
            padding: 1rem;
            margin-top: 0.5rem;
            backdrop-filter: blur(10px);
        ">
            <div style="display: flex; align-items: center; gap: 12px;">
                <div style="
                    width: 44px;
                    height: 44px;
                    border-radius: 12px;
                    background: linear-gradient(135deg, #3B82F6 0%, #06B6D4 100%);
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    color: white;
                    font-weight: 700;
                    font-size: 1.1rem;
                    box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
                    font-family: 'Outfit', sans-serif;
                ">{avatar_letter}</div>
                <div style="flex-grow: 1; overflow: hidden;">
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
                        margin-top: 2px;
                    ">
                        <span style="
                            width: 6px;
                            height: 6px;
                            background: #22C55E;
                            border-radius: 50%;
                            display: inline-block;
                        "></span>
                        <span style="
                            color: #22C55E;
                            font-size: 0.7rem;
                            font-weight: 500;
                        ">Active</span>
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # --- 7. SIGN OUT BUTTON ---
        st.markdown("<div style='height: 0.75rem'></div>", unsafe_allow_html=True)
        if st.button("🚪 Sign Out", type="secondary", width="stretch", key="logout_btn"):
            api.clear_session()
            st.rerun()
        
        # --- 8. VERSION FOOTER ---
        st.markdown("""
        <div style="
            text-align: center;
            padding-top: 1rem;
            color: #334155;
            font-size: 0.65rem;
            letter-spacing: 0.05em;
        ">
            v2.1 — © 2026 AI Healthcare
        </div>
        """, unsafe_allow_html=True)
    
    return selected
