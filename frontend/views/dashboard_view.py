import streamlit as st
from frontend.utils import api
from frontend.components import charts

def render_dashboard():
    # Styled header matching other pages
    username = st.session_state.get('username', 'User')
    st.markdown(f"""
    <div style="margin-bottom: 1.5rem;">
        <h2 style="margin:0; font-size: 1.75rem;">👋 Welcome back, {username}!</h2>
        <p style="color: #94A3B8; margin-top: 0.5rem;">
            Track your health trends and stay informed with personalized insights.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    st.subheader("📊 Your Health Trends")
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
    # Display static health tips
    st.markdown("""
    - **Stay Hydrated**: Drinking water is crucial for liver function.
    - **Regular Exercise**: 30 mins a day lowers diabetes risk.
    - **Sleep Well**: 7-8 hours of sleep improves heart health.
    """)
