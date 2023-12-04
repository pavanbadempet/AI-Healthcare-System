from nicegui import ui, app
from frontend.theme import load_theme
from frontend.components.sidebar import render_sidebar

def layout_page(func):
    """
    Decorator for authenticated pages.
    - Checks Login (redirects to / if missing).
    - Loads Theme.
    - Renders Sidebar.
    """
    def wrapper(*args, **kwargs):
        # 1. Auth Check
        if not app.storage.user.get('token'):
            ui.navigate.to('/')
            return
            
        # 2. Theme
        load_theme()
        
        # 3. Sidebar
        render_sidebar()
        
        # 4. Main Page Content (in a container)
        with ui.column().classes('w-full p-6'):
            func(*args, **kwargs)
            
    return wrapper
