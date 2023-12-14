from nicegui import ui
from frontend.layout import Layout
import time
from frontend.api import api

def prediction_layout_context(title, page_route):
    """
    Standard layout wrapper for all prediction pages.
    Provides the standard header, sidebar (via Layout), and a consistent container.
    """
    return Layout(title, current_path=page_route)

def result_display(result_data):
    """
    Standardized result display using Glassmorphism.
    result_data: dict with 'prediction', 'confidence' (optional), etc.
    """
    with ui.column().classes('w-full items-center gap-6 animate-fade-in'):
        
        # 1. Main Prediction Card
        with ui.element('div').classes('glass-card w-full max-w-2xl flex flex-col items-center p-8 gap-4 border-l-4 border-l-blue-400'):
            ui.label('Analysis Result').classes('text-lg font-medium text-gray-400 uppercase tracking-widest')
            
            pred = result_data.get('prediction', 'Unknown')
            is_risk = 'High' in pred or 'Positive' in pred or 'Yes' in pred
            
            color = 'text-red-400' if is_risk else 'text-green-400'
            icon = 'warning' if is_risk else 'check_circle'
            
            ui.icon(icon, size='4rem').classes(f'{color} mb-2')
            ui.label(pred).classes(f'text-4xl font-bold {color} text-center')
            
            if 'probability' in result_data:
                prob = result_data['probability']
                ui.label(f"Confidence: {prob:.1f}%").classes('text-sm text-gray-500')
                
                # Progress Bar
                with ui.row().classes('w-full h-3 bg-gray-700/50 rounded-full overflow-hidden mt-2'):
                    ui.element('div').classes(f'h-full {"bg-red-500" if is_risk else "bg-green-500"}').style(f'width: {prob}%')

        # 2. Recommendations / Disclaimer
        with ui.chat_message(avatar='https://cdn-icons-png.flaticon.com/512/4712/4712009.png', sent=False):
            ui.markdown(f"**AI Doctor:** Based on these results, {'please consult a specialist immediately.' if is_risk else 'you seem to be in good health. Keep it up!'}")
