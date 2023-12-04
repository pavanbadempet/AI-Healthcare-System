from nicegui import ui

# Exact Colors from Streamlit Theme
PRIMARY_COLOR = '#00d2ff'
BACKGROUND_COLOR = '#0e1117' # Streamlit Dark
SECONDARY_BG = '#262730'      # Sidebar Dark
TEXT_COLOR = '#fafafa'
FONT = 'sans-serif'

def load_theme():
    """Apply global theme to the current page."""
    # Set standard colors using Tailwind
    ui.colors(
        primary=PRIMARY_COLOR,
        secondary=SECONDARY_BG,
        accent=PRIMARY_COLOR,
        dark=BACKGROUND_COLOR,
        positive='#21c354',
        negative='#ff3333',
        info='#31ccec',
        warning='#f2c037'
    )
    
    # Global CSS injection for Modern Premium UI
    ui.add_head_html(f'''
        <style>
            :root {{
                --primary: {PRIMARY_COLOR};
                --secondary: {SECONDARY_BG};
                --bg: {BACKGROUND_COLOR};
            }}
            body {{
                background-color: {BACKGROUND_COLOR};
                background: linear-gradient(135deg, #0e1117 0%, #1a1c23 100%);
                color: {TEXT_COLOR};
                font-family: 'Inter', {FONT};
                overflow-x: hidden;
            }}
            .nicegui-content {{
                padding: 0;
                margin: 0;
                max_width: 100%;
            }}
            /* Glassmorphism Card */
            .glass-card {{
                background: rgba(30, 32, 40, 0.6);
                backdrop-filter: blur(12px);
                -webkit-backdrop-filter: blur(12px);
                border: 1px solid rgba(255, 255, 255, 0.08);
                box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3);
                border-radius: 16px;
                transition: transform 0.2s ease, box-shadow 0.2s ease;
            }}
            .glass-card:hover {{
                transform: translateY(-2px);
                box-shadow: 0 12px 40px 0 rgba(0, 210, 255, 0.1);
                border-color: rgba(0, 210, 255, 0.3);
            }}
            
            /* Sidebar Modernization */
            .q-drawer {{
                background: rgba(20, 22, 28, 0.95) !important;
                border-right: 1px solid rgba(255, 255, 255, 0.05);
            }}
            
            /* Inputs */
            .q-field__label {{
                color: #a0a0a0 !important;
            }}
            .q-field--outlined .q-field__control:before {{
                border-color: rgba(255, 255, 255, 0.1);
            }}
            
            /* Animations */
            @keyframes fadeIn {{
                from {{ opacity: 0; transform: translateY(10px); }}
                to {{ opacity: 1; transform: translateY(0); }}
            }}
            .animate-fade {{
                animation: fadeIn 0.6s ease-out forwards;
            }}
            
            /* Typography */
            h1, h2, h3, h4, h5, h6 {{
                letter-spacing: -0.5px;
            }}
        </style>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap" rel="stylesheet">
    ''')
