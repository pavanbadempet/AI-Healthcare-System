import streamlit as st
from frontend.utils.api import get_prediction, save_record, get_explanation
from frontend.components.charts import render_radar_chart

def render_kidney_page():
    st.markdown("""
<div style="margin-bottom: 2rem;">
    <h2 style="margin:0; font-size: 1.75rem;">🦠 Kidney Function Screening</h2>
    <p style="color: #94A3B8; margin-top: 0.5rem;">
        Screen for renal health indicators using clinical test values.
    </p>
</div>
""", unsafe_allow_html=True)

    with st.form("kidney_form"):
        # Section 1: Demographics & Vitals
        st.subheader("Patient Details")
        c1, c2, c3 = st.columns(3)
        with c1:
            age = st.number_input("Age", 1, 120, 50)
        with c2:
            bp = st.number_input("Blood Pressure (mm/Hg)", 50.0, 200.0, 80.0)
        with c3:
            sg = st.selectbox("Specific Gravity", [1.005, 1.010, 1.015, 1.020, 1.025])

        # Section 2: Laboratory Results
        st.subheader("Lab Reports")
        l1, l2, l3, l4 = st.columns(4)
        with l1:
            al = st.selectbox("Albumin (0-5)", [0, 1, 2, 3, 4, 5])
            su = st.selectbox("Sugar (0-5)", [0, 1, 2, 3, 4, 5])
            bgr = st.number_input("Blood Glucose Random", 50.0, 500.0, 120.0)
        with l2:
            bu = st.number_input("Blood Urea", 10.0, 300.0, 36.0)
            sc = st.number_input("Serum Creatinine", 0.0, 50.0, 1.2)
            sod = st.number_input("Sodium", 100.0, 200.0, 135.0)
        with l3:
            pot = st.number_input("Potassium", 1.0, 10.0, 4.0)
            hemo = st.number_input("Hemoglobin", 3.0, 20.0, 15.0)
            pcv = st.number_input("Packed Cell Volume", 10.0, 60.0, 44.0)
        with l4:
            wc = st.number_input("White Blood Cell Count", 1000.0, 30000.0, 7800.0)
            rc = st.number_input("Red Blood Cell Count", 1.0, 10.0, 5.2)

        # Section 3: Medical History & Symptoms
        st.subheader("History & Status")
        m1, m2, m3 = st.columns(3)
        with m1:
            rbc = st.selectbox("Red Blood Cells (Urine)", ["normal", "abnormal"])
            pc = st.selectbox("Pus Cells", ["normal", "abnormal"])
            pcc = st.selectbox("Pus Cell Clumps", ["notpresent", "present"])
            ba = st.selectbox("Bacteria", ["notpresent", "present"])
        with m2:
            htn = st.selectbox("Hypertension", ["no", "yes"])
            dm = st.selectbox("Diabetes Mellitus", ["no", "yes"])
            cad = st.selectbox("Coronary Artery Disease", ["no", "yes"])
        with m3:
            appet = st.selectbox("Appetite", ["good", "poor"])
            pe = st.selectbox("Pedal Edema", ["no", "yes"])
            ane = st.selectbox("Anemia", ["no", "yes"])

        if st.form_submit_button("Predict Kidney Health"):
            # Map inputs to Schema
            data = {
                "age": age, "bp": bp, "sg": sg, "al": al, "su": su,
                "rbc": 1 if rbc == "abnormal" else 0,
                "pc": 1 if pc == "abnormal" else 0,
                "pcc": 1 if pcc == "present" else 0,
                "ba": 1 if ba == "present" else 0,
                "bgr": bgr, "bu": bu, "sc": sc, "sod": sod, "pot": pot, 
                "hemo": hemo, "pcv": pcv, "wc": wc, "rc": rc,
                "htn": 1 if htn == "yes" else 0,
                "dm": 1 if dm == "yes" else 0,
                "cad": 1 if cad == "yes" else 0,
                "appet": 1 if appet == "poor" else 0, # Assuming 0 is good, need to verify. Usually 1 is bad.
                "pe": 1 if pe == "yes" else 0,
                "ane": 1 if ane == "yes" else 0
            }
            # Note on mapping: verify standard. Usually 1=Yes/Abnormal.
            
            with st.spinner("Analyzing..."):
                result = get_prediction("kidney", data)
                
            if "error" in result:
                st.error(result['error'])
            else:
                pred = result.get('prediction', 'Unknown')
                st.success(f"Result: **{pred}**")
                save_record("Kidney", data, pred)
                
                c1, c2 = st.columns(2)
                with c1: render_radar_chart(data)
                with c2: 
                    html = get_explanation("kidney", data)
                    if html: st.components.v1.html(html, height=300, scrolling=True)
