import streamlit as st
from frontend.utils import api

def render_profile_page():
    st.title(f"User Profile: {st.session_state.get('username')}")
    
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
