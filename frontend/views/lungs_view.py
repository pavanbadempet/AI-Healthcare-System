import streamlit as st
from frontend.utils.api import get_prediction, save_record, get_explanation
from frontend.components.charts import render_radar_chart

def render_lungs_page():
    st.markdown("""
<div style="margin-bottom: 2rem;">
    <h2 style="margin:0; font-size: 1.75rem;">🫁 Respiratory Health Screening</h2>
    <p style="color: #94A3B8; margin-top: 0.5rem;">
        A self-assessment tool for lung cancer risk factors and symptoms.
    </p>
</div>
""", unsafe_allow_html=True)

    with st.form("lungs_form"):
        col1, col2 = st.columns(2)
        with col1:
            age = st.number_input("Age", 0, 120, 60)
            gender = st.selectbox("Gender", ["Male", "Female"])
        
        st.subheader("Symptoms & Habits")
        
        # Grid layout for many checkboxes
        c1, c2, c3 = st.columns(3)
        with c1:
            smoking = st.checkbox("Smoking History")
            yellow_fingers = st.checkbox("Yellow Fingers")
            anxiety = st.checkbox("Anxiety")
            peer_pressure = st.checkbox("Peer Pressure")
            chronic_disease = st.checkbox("Chronic Disease")
        with c2:
            fatigue = st.checkbox("Fatigue / Tiredness")
            allergy = st.checkbox("Allergies")
            wheezing = st.checkbox("Wheezing")
            alcohol = st.checkbox("Alcohol Consumption")
            coughing = st.checkbox("Persistent Coughing")
        with c3:
            shortness_of_breath = st.checkbox("Shortness of Breath")
            swallowing_difficulty = st.checkbox("Swallowing Difficulty")
            chest_pain = st.checkbox("Chest Pain")

        if st.form_submit_button("Assess Risk"):
            # Map inputs (usually 1=No, 2=Yes in some datasets, or 0/1. 
            # Reviewing my test_api.py, I used 0/1 for binary. 
            # In backend/schemas.py LungsInput uses int.
            # Assuming standard 0=No, 1=Yes)
            
            data = {
                "gender": 1 if gender == "Male" else 0,
                "age": age,
                "smoking": int(smoking),
                "yellow_fingers": int(yellow_fingers),
                "anxiety": int(anxiety),
                "peer_pressure": int(peer_pressure),
                "chronic_disease": int(chronic_disease),
                "fatigue": int(fatigue),
                "allergy": int(allergy),
                "wheezing": int(wheezing),
                "alcohol": int(alcohol),
                "coughing": int(coughing),
                "shortness_of_breath": int(shortness_of_breath),
                "swallowing_difficulty": int(swallowing_difficulty),
                "chest_pain": int(chest_pain)
            }
            
            with st.spinner("Analyzing..."):
                result = get_prediction("lungs", data)
                
            if "error" in result:
                st.error(result['error'])
            else:
                pred = result.get('prediction', 'Unknown')
                st.success(f"Result: **{pred}**")
                save_record("Lungs", data, pred)
                
                c1, c2 = st.columns(2)
                with c1: render_radar_chart(data)
                with c2: 
                    html = get_explanation("lungs", data)
                    if html: st.components.v1.html(html, height=300, scrolling=True)
