import streamlit as st
from frontend.utils import api
from frontend.components import charts

def render_dashboard():
    # Styled header matching other pages
    username = st.session_state.get('username', 'Patient')
    st.markdown(f"""
<div style="margin-bottom: 2rem;">
    <h2 style="margin:0; font-size: 1.75rem;">👋 Hello, {username}</h2>
    <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 0.5rem;">
        <p style="color: #94A3B8; margin: 0;">
            Your Personal Health AI is <span style="color: #10B981;">● Active</span> & Ready to Help.
        </p>
        <div style="background: rgba(59, 130, 246, 0.1); color: #60A5FA; padding: 4px 12px; border-radius: 6px; font-size: 0.85rem; border: 1px solid rgba(59, 130, 246, 0.2);">
            Patient Portal
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# ... (Lines 22-37 omitted) ...

    with col_a:
        st.subheader("💡 AI Health Tips")
        st.markdown("""
<div style="background: rgba(15, 23, 42, 0.6); padding: 1rem; border-radius: 8px; border: 1px solid rgba(255,255,255,0.05);">
<p style="color: #cbd5e1; font-size: 0.9rem;">Based on your recent activity:</p>
<ul style="color: #94A3B8; margin-bottom: 0;">
    <li><b>Heart Health:</b> Your BMI is stable. Keep walking 30 mins/day.</li>
    <li><b>Diet:</b> Limit sugar intake before your next glucose test.</li>
    <li><b>Hydration:</b> Drink 2L water daily to support liver function.</li>
</ul>
</div>
""", unsafe_allow_html=True)

    with col_b:
        st.subheader("🔔 Notifications")
        st.markdown("""
<div style="background: rgba(15, 23, 42, 0.6); padding: 1rem; border-radius: 8px; border: 1px solid rgba(255,255,255,0.05);">
<div style="font-size: 0.9rem; margin-bottom: 0.5rem; color: #cbd5e1;"><b>Next Appointment:</b> No upcoming visits.</div>
<div style="font-size: 0.9rem; color: #cbd5e1;"><b>Report Status:</b> All reports are up to date.</div>
</div>
""", unsafe_allow_html=True)
    
    st.subheader("📈 My Health Trends")
    records = api.fetch_records()
    if records:
        tab1, tab2, tab3 = st.tabs(["BMI", "Glucose", "Bilirubin"])
        with tab1: charts.render_trend_chart(records, "bmi", "BMI")
        with tab2: charts.render_trend_chart(records, "blood_glucose_level", "Glucose")
        with tab3: charts.render_trend_chart(records, "total_bilirubin", "Bilirubin")
    else:
        st.info("No test results found. Visit your specialist to upload new diagnostic data.")

    st.markdown("---")
    col_a, col_b = st.columns(2)
    
    with col_a:
        st.subheader("💡 AI Health Tips")
        st.markdown("""
        <div style="background: rgba(15, 23, 42, 0.6); padding: 1rem; border-radius: 8px; border: 1px solid rgba(255,255,255,0.05);">
        <p style="color: #cbd5e1; font-size: 0.9rem;">Based on your recent activity:</p>
        <ul style="color: #94A3B8; margin-bottom: 0;">
            <li><b>Heart Health:</b> Your BMI is stable. Keep walking 30 mins/day.</li>
            <li><b>Diet:</b> Limit sugar intake before your next glucose test.</li>
            <li><b>Hydration:</b> Drink 2L water daily to support liver function.</li>
        </ul>
        </div>
        """, unsafe_allow_html=True)

    with col_b:
        st.subheader("🔔 Notifications")
        st.markdown("""
        <div style="background: rgba(15, 23, 42, 0.6); padding: 1rem; border-radius: 8px; border: 1px solid rgba(255,255,255,0.05);">
        <div style="font-size: 0.9rem; margin-bottom: 0.5rem; color: #cbd5e1;"><b>Next Appointment:</b> No upcoming visits.</div>
        <div style="font-size: 0.9rem; color: #cbd5e1;"><b>Report Status:</b> All reports are up to date.</div>
        </div>
        """, unsafe_allow_html=True)
