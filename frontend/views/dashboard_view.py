import streamlit as st
from frontend.utils import api
from frontend.components import charts

def render_dashboard():
    # Styled header matching other pages
    username = st.session_state.get('username', 'User')
    st.markdown(f"""
    <div style="margin-bottom: 2rem;">
        <h2 style="margin:0; font-size: 1.75rem;">🏥 Facility Dashboard</h2>
        <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 0.5rem;">
            <p style="color: #94A3B8; margin: 0;">
                Overview for <b>{username}</b> • System Status: <span style="color: #10B981;">● Online</span>
            </p>
            <div style="background: rgba(59, 130, 246, 0.1); color: #60A5FA; padding: 4px 12px; border-radius: 6px; font-size: 0.85rem; border: 1px solid rgba(59, 130, 246, 0.2);">
                Clinical OS v2.4
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.subheader("📉 Patient Vitals Analytics")
    records = api.fetch_records()
    if records:
        tab1, tab2, tab3 = st.tabs(["BMI", "Glucose", "Bilirubin"])
        with tab1: charts.render_trend_chart(records, "bmi", "BMI")
        with tab2: charts.render_trend_chart(records, "blood_glucose_level", "Glucose")
        with tab3: charts.render_trend_chart(records, "total_bilirubin", "Bilirubin")
    else:
        st.info("No patient data recorded in main register. Run a diagnostic screening to populate analytics.")

    st.markdown("---")
    col_a, col_b = st.columns(2)
    
    with col_a:
        st.subheader("📋 Clinical Protocols")
        st.markdown("""
        <div style="background: rgba(15, 23, 42, 0.6); padding: 1rem; border-radius: 8px; border: 1px solid rgba(255,255,255,0.05);">
        <ul style="color: #cbd5e1; margin-bottom: 0;">
            <li><b>Diabetic Screening:</b> Recommend HbA1c for patients > 45.</li>
            <li><b>Hypertension:</b> Monitor BP for all cardiac risk patients.</li>
            <li><b>Liver Panel:</b> Check bilirubin trends for early detection.</li>
        </ul>
        </div>
        """, unsafe_allow_html=True)

    with col_b:
        st.subheader("📢 System Announcements")
        st.markdown("""
        <div style="background: rgba(15, 23, 42, 0.6); padding: 1rem; border-radius: 8px; border: 1px solid rgba(255,255,255,0.05);">
        <div style="font-size: 0.9rem; margin-bottom: 0.5rem;"><b>New Feature:</b> Renal Failure Prediction Model v2.1 deployed.</div>
        <div style="font-size: 0.9rem;"><b>Maintenance:</b> Scheduled downtime Sunday 2 AM - 4 AM.</div>
        </div>
        """, unsafe_allow_html=True)
