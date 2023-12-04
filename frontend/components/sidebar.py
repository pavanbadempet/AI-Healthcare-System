from nicegui import ui, app

def render_sidebar():
    """Render the persistent sidebar navigation."""
    
    with ui.left_drawer(value=True).classes('bg-secondary text-white q-pa-md') as drawer:
        # User Profile Section (Top)
        with ui.column().classes('items-center w-full mb-6'):
            ui.avatar('account_circle', size='xl', color='primary', text_color='white')
            
            # Get username from storage (safe access)
            username = app.storage.user.get('username', 'Guest')
            ui.label(username).classes('text-lg font-bold mt-2')
            ui.label('Patient').classes('text-xs text-gray-400')
            
        ui.separator().classes('bg-gray-700 mb-4')
        
        # Navigation Links
        def nav_link(text, icon, target):
            """Helper for consistent nav links."""
            # Highlight active link logic could go here
            with ui.link(target=target).classes('w-full no-underline text-white hover:text-primary mb-2'):
                with ui.row().classes('items-center gap-4 p-2 rounded hover:bg-gray-800 transition-colors'):
                    ui.icon(icon).classes('text-xl')
                    ui.label(text).classes('text-sm')

        nav_link('Dashboard', 'dashboard', '/dashboard')
        
        ui.label('Health Predictions').classes('text-xs text-gray-500 mt-4 mb-2 font-bold')
        nav_link('Diabetes Check', 'water_drop', '/predict/diabetes')
        nav_link('Heart Health', 'favorite', '/predict/heart')
        nav_link('Liver Scans', 'medical_services', '/predict/liver')
        nav_link('Kidney Health', 'healing', '/predict/kidney')
        nav_link('Respiratory', 'air', '/predict/lungs')
        
        ui.separator().classes('bg-gray-700 my-4')
        
        nav_link('Smart Lab Report', 'analytics', '/report')
        nav_link('AI Chatbot', 'smart_toy', '/chat')
        
        # Logout
        ui.separator().classes('bg-gray-700 mt-auto mb-4')
        def logout():
            app.storage.user.clear()
            ui.navigate.to('/')
            
        with ui.button(on_click=logout).classes('w-full bg-red-500 flat text-white hover:bg-red-600'):
            with ui.row().classes('items-center gap-2'):
                ui.icon('logout')
                ui.label('Logout')
