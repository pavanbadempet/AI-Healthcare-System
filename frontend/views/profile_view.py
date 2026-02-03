import streamlit as st
from frontend.utils import api

def render_profile_page():
    username = st.session_state.get('username', 'Patient')
    st.markdown(f"""
<div style="margin-bottom: 2rem;">
    <h2 style="margin:0; font-size: 1.75rem;">👤 My Health Passport</h2>
    <p style="color: #94A3B8; margin-top: 0.5rem;">
        Your central hub for personal health data and system preferences.
    </p>
</div>
""", unsafe_allow_html=True)
    
    profile = api.fetch_profile()
    if not profile:
        st.error("Could not load profile.")
        return

    with st.expander("📝 Edit Profile Details", expanded=False):
        with st.form("profile_update"):
            col1, col2 = st.columns(2)
            with col1:
                height = st.number_input("Height (cm)", value=float(profile.get("height") or 170.0))
                weight = st.number_input("Weight (kg)", value=float(profile.get("weight") or 70.0))
                diet = st.selectbox("Diet", ["Vegetarian", "Non-Vegetarian", "Vegan", "Keto", "Other"], index=0 if not profile.get("diet") else ["Vegetarian", "Non-Vegetarian", "Vegan", "Keto", "Other"].index(profile.get("diet")))
            with col2:
                activity = st.selectbox("Activity Level", ["Sedentary", "Lightly Active", "Moderately Active", "Very Active"], index=0)
                sleep = st.slider("Sleep (Hours)", 4.0, 12.0, float(profile.get("sleep_hours") or 7.0))
                stress = st.selectbox("Stress Level", ["Low", "Moderate", "High"], index=1)
                
            allow_data = st.checkbox("Allow Data Collection for AI Improvement", value=profile.get("allow_data_collection", True))
            
            if st.form_submit_button("Update Profile"):
                payload = {
                    "height": height, "weight": weight, "diet": diet,
                    "activity_level": activity, "sleep_hours": sleep,
                    "stress_level": stress, "allow_data_collection": allow_data
                }
                api.update_profile(payload)
                st.rerun()

    # Display Metrics
    st.markdown("### My Stats")
    c1, c2, c3 = st.columns(3)
    c1.metric("Height", f"{profile.get('height') or 0} cm")
    c2.metric("Weight", f"{profile.get('weight') or 0} kg")
    
    # Calculate BMI
    height_val = profile.get('height') or 170
    weight_val = profile.get('weight') or 70
    
    h_m = float(height_val) / 100
    w_kg = float(weight_val)
    bmi = round(w_kg / (h_m ** 2), 2)
    c3.metric("BMI", bmi, delta="Normal" if 18.5 <= bmi <= 25 else "Check", delta_color="normal" if 18.5 <= bmi <= 25 else "inverse")

    # --- PDF Health Report Download ---
    st.markdown("---")
    st.markdown("### 📄 Download Health Report")
    st.markdown("""
    <p style="color: #94A3B8; font-size: 0.9rem;">
        Download a PDF summary of your health profile and assessment history.
    </p>
    """, unsafe_allow_html=True)
    
    # Download button with link to backend endpoint
    backend_url = api.get_backend_url()
    token = st.session_state.get('token', '')
    
    col1, col2 = st.columns([1, 3])
    with col1:
        st.markdown(f"""
        <a href="{backend_url}/download/health-report" target="_blank" style="text-decoration: none;">
            <button style="
                background: linear-gradient(135deg, #3B82F6, #8B5CF6);
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 8px;
                font-weight: 600;
                cursor: pointer;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            ">
                📥 Download PDF Report
            </button>
        </a>
        """, unsafe_allow_html=True)
    
    with col2:
        st.info("💡 **Tip:** The PDF includes your profile, recent health assessments, and personalized recommendations.")

    # --- Personalized Health Tips ---
    st.markdown("---")
    st.markdown("### 💡 Your Personalized Tips")
    
    tips = []
    if bmi < 18.5:
        tips.append("🍎 Your BMI suggests you're underweight. Consider consulting a nutritionist for a healthy weight gain plan.")
    elif bmi > 25:
        tips.append("🏃 Your BMI is above normal. Regular cardio exercise and a balanced diet can help maintain a healthy weight.")
    else:
        tips.append("✅ Great job! Your BMI is in the healthy range. Keep up your good habits!")
    
    if profile.get('sleep_hours') and float(profile.get('sleep_hours', 7)) < 7:
        tips.append("😴 You're getting less than 7 hours of sleep. Quality sleep is crucial for heart health and immune function.")
    
    if profile.get('stress_level') == 'High':
        tips.append("🧘 High stress can impact your health. Consider meditation, deep breathing, or regular walks.")
    
    tips.append("💧 Remember to drink 8 glasses of water daily for optimal health.")
    tips.append("🩺 Schedule regular check-ups with your healthcare provider.")
    
    for tip in tips:
        st.markdown(f"- {tip}")

