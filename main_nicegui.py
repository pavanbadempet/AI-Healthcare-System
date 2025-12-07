import sys
import os
from nicegui import ui, app as nice_app
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

# Setup Paths
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import Backend (Existing Logic)
# from backend.main import app as backend_api
from frontend.theme import load_theme

# --- App Setup ---
def init_nicegui():
    """Initialize NiceGUI"""
    
    # 1. Mount Backend? NO. We run backend separately on port 8000.
    # nice_app.mount("/api", backend_api)
    
    # 2. Main Page (Router)
    @ui.page('/')
    def main_page():
        from frontend.pages.login import login_page
        login_page()
        
    @ui.page('/dashboard')
    def dashboard_route():
        from frontend.pages.dashboard import dashboard_page
        dashboard_page()
            
    # 3. Startup
    ui.run(
        title="AIO Healthcare System",
        favicon="🏥",
        dark=True,
        port=8080, # Distinct from Streamlit (8501) and Backend (8000)
        show=False,
        storage_secret='healthcare_secret_key_123'
    )

if __name__ in {"__main__", "__mp_main__"}:
    init_nicegui()
