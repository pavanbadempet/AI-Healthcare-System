import streamlit as st
from frontend.utils import api
from frontend.components import charts

def render_diabetes_page():
    st.header("🩸 Diabetes Risk Assessment")
    st.markdown("Enter your health details below for an AI-powered assessment.")

    col1, col2 = st.columns(2)
    with col1:
        gender = st.selectbox("Gender", ["Female", "Male"])
        age = st.number_input("Age", 1, 120, 30)
        bmi = st.number_input("BMI", 10.0, 50.0, 25.0)
        hba1c = st.number_input("HbA1c Level", 0.0, 15.0, 5.5)
        glucose = st.number_input("Blood Glucose Level", 50, 300, 100)
    
    with col2:
        hypertension = st.selectbox("Hypertension", ["No", "Yes"])
        heart_disease = st.selectbox("Heart Disease", ["No", "Yes"])
        smoking = st.selectbox("Smoking History", ["never", "current", "former", "ever", "not current"])
        # Hidden defaults for cleaner UI if not available, or expose if critical
        # The schema requires: high_chol, physical_activity, general_health
        # Let's adding them as advanced or just exposed:
        high_chol = st.selectbox("High Cholesterol", ["No", "Yes"])
        activity = st.selectbox("Physically Active (Past 30d)", ["No", "Yes"])
        gen_health = st.slider("General Health (1=Excellent, 5=Poor)", 1, 5, 3)

    if st.button("Analyze Risk", type="primary"):
        # Map Inputs
        inputs = {
            "gender": 1 if gender == "Male" else 0,
            "age": age,
            "hypertension": 1 if hypertension == "Yes" else 0,
            "heart_disease": 1 if heart_disease == "Yes" else 0,
            "smoking_history": 0 if smoking == "never" else 1, # Simplified map, really strict map in schema needed? 
            # WAIT: Backend prediction.py schema for diabetes uses: smoking_history (int)
            # BUT ml_service.py (legacy) handled string mapping. 
            # IF we hit backend DIRECTLY (recommended), we need to send INTs.
            # Let's map robustly here or use `api` wrapper.
            # Schema says: smoking_history: int. 0: No, 1: Yes. 
            # Actually, `backend/schemas.py` says `smoking_history: int = Field(..., description="0: No, 1: Yes")`. 
            # Just 0/1. OK.
            "bmi": bmi,
            "high_chol": 1 if high_chol == "Yes" else 0,
            "physical_activity": 1 if activity == "Yes" else 0,
            "general_health": gen_health,
        }
        
        # Override smoking mapping if the user chose specific strings? 
        # Schema documentation was "0: No, 1: Yes". 
        # Ideally, we should trust the schema.
        
        with st.spinner("Analyzing..."):
            result = api.get_prediction("diabetes", inputs)
        
        if "error" in result:
            st.error(f"Error: {result['error']}")
        else:
            prediction = result.get("prediction", "Unknown")
            st.success(f"Result: **{prediction}**")
            
            # Save Record
            api.save_record("Diabetes", inputs, prediction)
            
            # Show Charts
            st.markdown("---")
            c1, c2 = st.columns(2)
            with c1:
                st.subheader("Risk Profile")
                charts.render_radar_chart(inputs)
            with c2:
                st.subheader("Explanation (SHAP)")
                html = api.get_explanation("diabetes", inputs)
                if html:
                    st.components.v1.html(html, height=300, scrolling=True)
