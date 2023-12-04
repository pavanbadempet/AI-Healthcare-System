from nicegui import ui, app
from frontend.theme import load_theme, PRIMARY_COLOR, SECONDARY_BG, TEXT_COLOR
import requests

def login_page():
    """Render the Modern Login Page."""
    load_theme()
    
    with ui.row().classes('w-full h-screen p-0 m-0 no-wrap'):
        
        # Left Section: Hero / Branding (60% width)
        with ui.column().classes('w-full md:w-3/5 h-full items-center justify-center p-12 relative-position hidden md:flex'):
            # Animated Gradient Background
            ui.html('<div style="position:absolute; inset:0; background: radial-gradient(circle at 30% 50%, #001f3f 0%, #0e1117 70%); z-index:0;"></div>')
            ui.html('<div style="position:absolute; top:20%; left:20%; width:300px; height:300px; background:#00d2ff; filter:blur(150px); opacity:0.15; border-radius:50%; z-index:1;"></div>')
            
            # Content
            with ui.column().classes('z-10 animate-fade'):
                ui.label('Next-Gen Healthcare AI').classes('text-5xl font-bold text-white mb-4 leading-tight')
                ui.label('Experience the power of Ensemble Models\nand Real-time Analytics.').classes('text-xl text-gray-300 mb-8 whitespace-pre-line')
                
                with ui.row().classes('gap-4'):
                    with ui.row().classes('items-center gap-2 bg-white/5 rounded-lg px-4 py-2 border border-white/10'):
                        ui.icon('speed').classes('text-primary')
                        ui.label('Real-time Prediction')
                    with ui.row().classes('items-center gap-2 bg-white/5 rounded-lg px-4 py-2 border border-white/10'):
                        ui.icon('security').classes('text-primary')
                        ui.label('HIPAA Compliant')
        
        # Right Section: Login Form (40% width)
        with ui.column().classes('w-full md:w-2/5 h-screen items-center justify-center bg-[#0e1117] relative-position p-8'):
            
            # Form Container
            with ui.card().classes('w-full max-w-sm p-8 glass-card animate-fade gap-6'):
                
                # Header
                with ui.column().classes('items-center w-full mb-2'):
                    ui.icon('health_and_safety').classes('text-5xl text-primary mb-2')
                    ui.label('Welcome Back').classes('text-2xl font-bold text-white')
                    ui.label('Sign in to access your dashboard').classes('text-sm text-gray-400')
                
                # Inputs
                username = ui.input('Username').classes('w-full').props('outlined dense dark start-icon=person color=primary')
                password = ui.input('Password', password=True, password_toggle_button=True).classes('w-full').props('outlined dense dark start-icon=lock color=primary')
                
                # Status
                status = ui.label('').classes('text-red-400 text-xs h-4 self-center')
                
                def try_login():
                    if not username.value or not password.value:
                        status.set_text("Please enter credentials.")
                        return
                    
                    status.set_text("Authenticating...")
                    try:
                        response = requests.post(
                            "http://127.0.0.1:8000/token",
                            data={"username": username.value, "password": password.value}
                        )
                        
                        if response.status_code == 200:
                            token = response.json().get("access_token")
                            app.storage.user['token'] = token
                            app.storage.user['username'] = username.value
                            ui.navigate.to('/dashboard')
                        else:
                            status.set_text("Invalid Credentials.")
                            
                    except Exception as e:
                        status.set_text("Server Unreachable")

                # Action Button
                ui.button('Sign In', on_click=try_login).classes('w-full bg-gradient-to-r from-cyan-500 to-blue-600 text-white font-bold h-10 shadow-lg hover:shadow-cyan-500/50 transition-all rounded-lg')
                
                # Footer
                ui.label('Powered by AIO Health System').classes('text-[10px] text-gray-600 self-center mt-4')

