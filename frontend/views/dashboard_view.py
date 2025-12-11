import streamlit as st
from frontend.utils import api
from frontend.components import charts

def render_dashboard():
    st.header(f"👋 Welcome back, {st.session_state.get('username', 'User')}!")
    
    # Quick Stats or Alerts can go here
    
    st.subheader("Your Health Trends")
    records = api.fetch_records()
    if records:
        tab1, tab2, tab3 = st.tabs(["BMI", "Glucose", "Bilirubin"])
        with tab1: charts.render_trend_chart(records, "bmi", "BMI")
        with tab2: charts.render_trend_chart(records, "blood_glucose_level", "Glucose")
        with tab3: charts.render_trend_chart(records, "total_bilirubin", "Bilirubin")
    else:
        st.info("No records found. Take a prediction test to track your health!")

    st.markdown("---")
    st.subheader("Latest Health News")
    # For now, placeholder or fetch logic from original main.py if critical.
    # Original main.py had 'fetch_news_feed'. 
    # To keep it simple for optimization, we can display static helpful tips or implement the fetcher if needed.
    st.markdown("""
    - **Stay Hydrated**: Drinking water is crucial for liver function.
    - **Regular Exercise**: 30 mins a day lowers diabetes risk.
    - **Sleep Well**: 7-8 hours of sleep improves heart health.
    """)
