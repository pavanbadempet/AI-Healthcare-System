from nicegui import ui, app
from frontend.layout import layout_page
import random

# Mock Data for Dashboard
def get_mock_trend_data():
    """Generate dummy trend data for EChart."""
    days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    sugar = [random.randint(90, 140) for _ in range(7)]
    bp = [random.randint(110, 130) for _ in range(7)]
    return days, sugar, bp

def get_mock_news():
    """Dummy News Feed."""
    return [
        {"title": "Breakthrough in Diabetes Mgmt", "date": "2 hours ago", "source": "Medical News"},
        {"title": "Heart Health: New Guidelines", "date": "Yesterday", "source": "CDC"},
        {"title": "Liver Enzyme Research", "date": "2 days ago", "source": "Nature"},
    ]

@layout_page
def dashboard_page():
    """Render the Main Dashboard."""
    
    # 1. Header with Name
    username = app.storage.user.get('username', 'Patient')
    ui.label(f"Welcome back, {username}!").classes('text-3xl font-bold mb-6 text-white')
    
    # 2. Key Metrics Row
    with ui.row().classes('w-full gap-4 mb-8'):
        def metric_card(title, value, unit, color, icon):
            with ui.card().classes(f'w-64 p-4 border-l-4 border-{color} bg-secondary'):
                with ui.row().classes('items-center justify-between w-full'):
                    with ui.column():
                        ui.label(title).classes('text-gray-400 text-sm')
                        with ui.row().classes('items-baseline gap-1'):
                            ui.label(value).classes('text-2xl font-bold text-white')
                            ui.label(unit).classes('text-xs text-gray-500')
                    ui.icon(icon).classes(f'text-3xl text-{color} opacity-80')
                    
        metric_card("Last Glucose", "108", "mg/dL", "green", "water_drop")
        metric_card("Blood Pressure", "120/80", "mmHg", "red", "favorite")
        metric_card("Risk Factor", "Low", "Score", "blue", "analytics")
        
    # 3. Main Content Grid (Charts + News)
    with ui.row().classes('w-full gap-6'):
        
        # Left: Health Trend Chart
        with ui.card().classes('w-full md:w-2/3 bg-secondary p-4'):
            ui.label('Weekly Health Trends').classes('text-lg font-bold mb-4 text-white')
            
            days, sugar, bp = get_mock_trend_data()
            
            ui.echart({
                'tooltip': {'trigger': 'axis'},
                'legend': {'textStyle': {'color': '#ccc'}},
                'xAxis': {
                    'type': 'category', 
                    'data': days,
                    'axisLabel': {'color': '#ccc'}
                },
                'yAxis': {
                    'type': 'value',
                    'axisLabel': {'color': '#ccc'}
                },
                'series': [
                    {
                        'name': 'Glucose',
                        'type': 'line',
                        'data': sugar,
                        'smooth': True,
                        'color': '#ff4d4f'
                    },
                    {
                        'name': 'Systolic BP',
                        'type': 'line',
                        'data': bp,
                        'smooth': True,
                        'color': '#1890ff'
                    }
                ]
            }).classes('h-64 w-full')

        # Right: News Feed
        with ui.card().classes('w-full md:w-1/4 bg-secondary p-4 flex-grow'):
            ui.label('Latest Updates').classes('text-lg font-bold mb-4 text-white')
            
            with ui.scroll_area().classes('h-64 w-full pr-4'):
                news = get_mock_news()
                for item in news:
                    with ui.column().classes('mb-4 pb-2 border-b border-gray-700 w-full'):
                        ui.label(item['title']).classes('font-bold text-sm text-blue-400 cursor-pointer')
                        with ui.row().classes('justify-between w-full'):
                            ui.label(item['source']).classes('text-xs text-gray-400')
                            ui.label(item['date']).classes('text-xs text-gray-500')

