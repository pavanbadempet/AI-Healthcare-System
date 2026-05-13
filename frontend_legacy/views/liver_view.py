import streamlit as st
from frontend.utils import api
from frontend.components import charts

def render_liver_page():
    st.markdown("""
<div style="margin-bottom: 2rem;">
    <h2 style="margin:0; font-size: 1.75rem;">🥃 Liver Health Screening</h2>
    <p style="color: #94A3B8; margin-top: 0.5rem;">
        Analyze liver function markers from your latest blood panel.
    </p>
</div>
""", unsafe_allow_html=True)
    
    profile = api.fetch_profile() or {}
    
    # 1. Age Calculation
    default_age = 45
    if profile.get('dob'):
        try:
            from datetime import datetime
            birth_date = datetime.strptime(str(profile['dob']).split()[0], "%Y-%m-%d")
            today = datetime.today()
            default_age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
        except:
            pass

    # 2. Gender
    p_gender = profile.get('gender', 'Male')
    gender_idx = 0 if p_gender == "Female" else 1

    col1, col2 = st.columns(2)
    with col1:
        age = st.number_input("Age", 1, 120, default_age)
        gender = st.selectbox("Gender", ["Female", "Male"], index=gender_idx)
        tot_bili = st.number_input("Total Bilirubin", 0.0, 50.0, 1.0)
        alk_phos = st.number_input("Alkaline Phosphotase", 0.0, 2000.0, 100.0)
        alamine = st.number_input("Alamine Aminotransferase", 0.0, 2000.0, 30.0)
    
    with col2:
        albumin = st.number_input("Albumin", 0.0, 10.0, 3.0)
        ag_ratio = st.number_input("Albumin/Globulin Ratio", 0.0, 10.0, 1.0)
        # Extras (Hidden defaults or simple inputs)
        direct_bili = 0.5
        aspartate = 30.0
        total_prot = 6.0

    if st.button("Predict Liver Risk", type="primary"):
        inputs = {
            "age": float(age),
            "gender": 1 if gender == "Male" else 0,
            "total_bilirubin": tot_bili,
            "direct_bilirubin": direct_bili,
            "alkaline_phosphotase": alk_phos,
            "alamine_aminotransferase": alamine,
            "aspartate_aminotransferase": aspartate,
            "total_proteins": total_prot,
            "albumin": albumin,
            "albumin_and_globulin_ratio": ag_ratio
        }
        
        with st.spinner("Analyzing Liver..."):
            result = api.get_prediction("liver", inputs)
            
        if "error" in result:
            st.error(result['error'])
        else:
            prediction = result.get("prediction", "Unknown")
            st.success(f"Result: **{prediction}**")
            api.save_record("Liver", inputs, prediction)
            
            c1, c2 = st.columns(2)
            with c1: charts.render_radar_chart(inputs)
            with c2: 
                html = api.get_explanation("liver", inputs)
                if html: st.components.v1.html(html, height=300, scrolling=True)
