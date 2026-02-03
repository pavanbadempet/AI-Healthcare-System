"""
Telemedicine Consultation View
==============================
Book video appointments with doctors.
"""
import streamlit as st
from datetime import datetime, timedelta

def render_telemedicine_page():
    st.markdown("""
<div style="text-align: center; margin-bottom: 2rem;">
    <h1>🩺 Virtual Consultation</h1>
    <p style="color: #64748B;">Video consultations with your facility's specialists.</p>
</div>
""", unsafe_allow_html=True)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("### 📅 Book an Appointment")
        with st.form("booking_form"):
            specialist = st.selectbox("Select Specialist", [
                "General Physician (Dr. Smith)",
                "Cardiologist (Dr. A. Gupta)",
                "Endocrinologist (Dr. R. Lee)",
                "Nutritionist (Sarah Jones)"
            ])
            
            d = st.date_input("Preferred Date", min_value=datetime.today())
            t = st.time_input("Preferred Time", value=datetime.now())
            
            reason = st.text_area("Reason for Visit", placeholder="Describe your symptoms...")
            
            submitted = st.form_submit_button("Confirm Booking", type="primary")
            
            if submitted:
                st.success(f"✅ Appointment Confirmed with {specialist}!")
                st.info(f"📅 Scheduled for: {d} at {t}")
                st.write("🔗 A secure video link has been sent to your email.")
                st.balloons()
    
    with col2:
        st.markdown("### 🧬 Upcoming Sessions")
        st.info("No upcoming sessions.")
        
        st.markdown("### 📜 Past Consultations")
        st.caption("No history available.")
        
        st.markdown("---")
        st.markdown("### 🚑 Emergency?")
        st.error("Call 911 (US) or 102 (India) immediately.")
