import streamlit as st
from frontend.utils import api
from frontend.components import charts

def render_heart_page():
    st.markdown("""
<div style="margin-bottom: 2rem;">
    <h2 style="margin:0; font-size: 1.75rem;">❤️ Heart Health Screening</h2>
    <p style="color: #94A3B8; margin-top: 0.5rem;">
        Assess cardiovascular risk factors using metrics from your check-up.
    </p>
</div>
""", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        age = st.number_input("Age", 1, 120, 45)
        gender = st.selectbox("Gender", ["Female", "Male"])
        bmi = st.number_input("BMI", 10.0, 50.0, 25.0)
        systolic = st.number_input("Systolic BP", 80, 250, 120)
        chol = st.number_input("Cholesterol", 100, 600, 200)
    
    with col2:
        smoker = st.selectbox("Smoked 100+ cigs in lifetime?", ["No", "Yes"])
        stroke = st.selectbox("History of Stroke?", ["No", "Yes"])
        diabetes = st.selectbox("Diabetes History?", ["No", "Yes"])
        activity = st.selectbox("Physical Activity (Past 30d)", ["No", "Yes"])
        alcohol = st.selectbox("Heavy Alcohol Consumption?", ["No", "Yes"])
        general = st.slider("General Health", 1, 5, 3)

    if st.button("Predict Heart Risk", type="primary"):
        inputs = {
            "age": age,
            "gender": 1 if gender == "Male" else 0,
            "high_bp": 1 if systolic > 130 else 0,
            "high_chol": 1 if chol > 200 else 0,
            "bmi": bmi,
            "smoker": 1 if smoker == "Yes" else 0,
            "stroke": 1 if stroke == "Yes" else 0,
            "diabetes": 1 if diabetes == "Yes" else 0,
            "phys_activity": 1 if activity == "Yes" else 0,
            "hvy_alcohol": 1 if alcohol == "Yes" else 0,
            "gen_hlth": general
        }
        
        with st.spinner("Analyzing Heart Health..."):
            result = api.get_prediction("heart", inputs)
            
        if "error" in result:
            st.error(result['error'])
        else:
            prediction = result.get("prediction", "Unknown")
            st.success(f"Result: **{prediction}**")
            api.save_record("Heart", inputs, prediction)
            
            c1, c2 = st.columns(2)
            with c1: charts.render_radar_chart(inputs)
            with c2: 
                html = api.get_explanation("heart", inputs)
                if html: st.components.v1.html(html, height=300, scrolling=True)
