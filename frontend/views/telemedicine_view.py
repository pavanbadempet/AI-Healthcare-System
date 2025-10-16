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
            # Fetch Doctors Dynamic List
            from frontend.utils import api
            doctors = api.fetch_doctors()
            
            doctor_map = {}
            if doctors:
                for doc in doctors:
                    label = f"{doc['full_name']} - {doc['specialization']} (₹{doc['consultation_fee']})"
                    doctor_map[label] = doc
                    
                selected_label = st.selectbox("Select Specialist", list(doctor_map.keys()))
                selected_doc = doctor_map[selected_label]
            else:
                st.warning("No doctors are currently available. Using fallback.")
                selected_doc = None
                specialist = st.selectbox("Select Specialist", [
                     "General Physician (Dr. Smith)",
                     "Cardiologist (Dr. A. Gupta)"
                ])
            
            d = st.date_input("Preferred Date", min_value=datetime.today())
            t = st.time_input("Preferred Time", value=datetime.now())
            
            reason = st.text_area("Reason for Visit", placeholder="Describe your symptoms...")
            
            submitted = st.form_submit_button("Confirm Booking", type="primary")
            
            if submitted:
                if not reason:
                    st.error("Please provide a reason for your visit.")
                else:
                    specialist_name = selected_doc['full_name'] if selected_doc else specialist
                    doctor_id = selected_doc['id'] if selected_doc else None
                    
                    payload = {
                        "doctor_id": doctor_id,
                        "specialist": specialist_name,
                        "date": str(d),
                        "time": str(t),
                        "reason": reason
                    }
                    if api.book_appointment(payload):
                        st.success(f"✅ Appointment Confirmed with {specialist_name}!")
                        st.info("📧 Confirmation email has been sent.")
                        st.balloons()
                        st.rerun()
    
    with col2:
        st.markdown("### 🧬 Upcoming Sessions")
        
        from frontend.utils import api
        appointments = api.fetch_appointments()
        
        if appointments:
            for appt in appointments:
                 # Parse ISO format if needed, or just display raw for now
                 # Backend returns ISO datetime
                 date_str = appt['date_time'].replace("T", " ")[:16] # Simpler formatting
                 
                 st.info(f"""
**{appt['specialist']}**  
📅 {date_str}  
*{appt['status']}*
""")
        else:
            st.info("No upcoming sessions.")
        
        st.markdown("### 📜 Past Consultations")
        st.caption("No history available.")
        
        st.markdown("---")
        st.markdown("### 🚑 Emergency?")
        st.error("Call 911 (US) or 102 (India) immediately.")
