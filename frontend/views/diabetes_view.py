import streamlit as st
from frontend.utils import api
from frontend.components import charts

def render_diabetes_page():
    st.markdown("""
    <div style="margin-bottom: 2rem;">
        <h2 style="margin:0; font-size: 1.75rem;">🩸 Diabetes Health Screening</h2>
        <p style="color: #94A3B8; margin-top: 0.5rem;">
            Use your latest lab report to screen for potential diabetes indicators.
        </p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Patient Details")
        gender = st.selectbox("Gender", ["Female", "Male"])
        age = st.number_input("Age", 1, 120, 30)
        bmi = st.number_input("BMI (Body Mass Index)", 10.0, 50.0, 25.0)
        hba1c = st.number_input("HbA1c Level (From Lab Report)", 0.0, 15.0, 5.5, help="Hemoglobin A1c is your average blood sugar levels over the past 3 months.")
        glucose = st.number_input("Blood Glucose Level (mg/dL)", 50, 300, 100)
    
    with col2:
        st.subheader("Medical History")
        hypertension = st.selectbox("Hypertension (High BP)", ["No", "Yes"])
        heart_disease = st.selectbox("History of Heart Disease", ["No", "Yes"])
        smoking = st.selectbox("Smoking History", ["never", "current", "former", "ever", "not current"])
        # Advanced Inputs (Optional)
        with st.expander("Additional Health Factors", expanded=False):
            high_chol = st.selectbox("High Cholesterol", ["No", "Yes"])
            activity = st.selectbox("Physically Active (Past 30d)", ["No", "Yes"])
            gen_health = st.slider("General Health Rating", 1, 5, 3, help="1=Excellent, 5=Poor")

    if st.button("Run Screening Analysis", type="primary", width="stretch"):
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
            
            # --- Generative AI Explanation ---
            with st.spinner("Generating AI Health Insights..."):
                ai_resp = api.get_ai_explanation("Diabetes", inputs, prediction)
                
            if ai_resp:
                st.markdown("---")
                st.subheader("🤖 AI Health Analysis")
                
                # Explanation
                st.markdown(f"""
                <div style="
                    background: rgba(30, 41, 59, 0.5); 
                    border-left: 4px solid #3B82F6;
                    padding: 1rem;
                    border-radius: 4px;
                    margin-bottom: 1.5rem;
                ">
                    <h4 style="margin-top:0; color: #60A5FA;">Assessment</h4>
                    <p style="margin-bottom:0; color: #E2E8F0;">{ai_resp.get('explanation', '')}</p>
                </div>
                """, unsafe_allow_html=True)
                
                # Tips
                if ai_resp.get('lifestyle_tips'):
                    st.markdown("#### 💡 Personalized Recommendations")
                    for tip in ai_resp['lifestyle_tips']:
                        st.markdown(f"- {tip}")
