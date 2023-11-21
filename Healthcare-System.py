import pickle
import requests
import streamlit as st
from streamlit_option_menu import option_menu
import pandas as pd
import numpy as np
import json
import base64
from io import BytesIO
from streamlit_lottie import st_lottie

# --- Page Config ---
st.set_page_config(
    page_title="AIO Healthcare System",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Backend Configuration ---
BACKEND_URL = "http://localhost:8000"

# --- Load Custom CSS ---
def local_css(file_name):
    try:
        with open(file_name) as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
    except FileNotFoundError:
        pass # Handle missing css gracefully or recreate it

local_css("assets/style.css")

# --- Hide Streamlit Style ---
hide_st_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {
                visibility: visible;
                background-color: transparent;
            }
            [data-testid="stHeader"] {
                background-color: transparent;
            }
            /* Profile Picture Circle */
            .profile-pic {
                border-radius: 50%;
                width: 100px;
                height: 100px;
                object-fit: cover;
                display: block;
                margin-left: auto;
                margin-right: auto;
                border: 3px solid #00d2ff;
            }
            </style>
            """
st.markdown(hide_st_style, unsafe_allow_html=True)

# --- Helper Functions ---
def load_lottieurl(url):
    try:
        r = requests.get(url)
        if r.status_code != 200:
            return None
        return r.json()
    except:
        return None

def fetch_profile():
    if st.session_state.auth_token:
        headers = {"Authorization": f"Bearer {st.session_state.auth_token}"}
        try:
            res = requests.get(f"{BACKEND_URL}/profile", headers=headers)
            if res.status_code == 200:
                st.session_state.profile = res.json()
        except:
            pass

def update_profile(data):
    if st.session_state.auth_token:
        headers = {"Authorization": f"Bearer {st.session_state.auth_token}"}
        try:
            res = requests.put(f"{BACKEND_URL}/profile", json=data, headers=headers)
            if res.status_code == 200:
                st.session_state.profile = res.json().get("user")
                return True
        except:
            pass
    return False

def delete_record(record_id):
    if st.session_state.auth_token:
        headers = {"Authorization": f"Bearer {st.session_state.auth_token}"}
        try:
            res = requests.delete(f"{BACKEND_URL}/records/{record_id}", headers=headers)
            if res.status_code == 200:
                return True
        except:
            pass
    return False

# --- Load Models ---
@st.cache_resource
def load_models():
    try:
        diabetes_model = pickle.load(open("Diabetes Model.pkl", 'rb'))
        heart_disease_model = pickle.load(open("Heart Disease Model.pkl",'rb'))
        liver_model = pickle.load(open("Liver Disease Model.pkl", 'rb'))
        scaler = pickle.load(open("Scaler.pkl", 'rb'))
        return diabetes_model, heart_disease_model, liver_model, scaler
    except Exception as e:
        return None, None, None, None

diabetes_model, heart_disease_model, liver_model, scaler = load_models()

# --- Authentication State ---
if 'auth_token' not in st.session_state:
    st.session_state.auth_token = None
if 'username' not in st.session_state:
    st.session_state.username = None
if 'profile' not in st.session_state:
    st.session_state.profile = {}

# --- Auth Functions ---
SESSION_FILE = "session.json"

def save_session(token, username):
    try:
        with open(SESSION_FILE, "w") as f:
            json.dump({"token": token, "username": username}, f)
    except:
        pass

def load_session():
    try:
        with open(SESSION_FILE, "r") as f:
            return json.load(f)
    except:
        return None

def clear_session():
    try:
        import os
        if os.path.exists(SESSION_FILE):
            os.remove(SESSION_FILE)
    except:
        pass

def login(username, password):
    try:
        res = requests.post(f"{BACKEND_URL}/token", data={"username": username, "password": password})
        if res.status_code == 200:
            data = res.json()
            save_session(data["access_token"], username) # Auto-save on login
            return data
        return None
    except:
        return None

def signup(username, password):
    try:
        res = requests.post(f"{BACKEND_URL}/signup", json={"username": username, "password": password})
        if res.status_code == 200:
            return True, None
        return False, res.text
    except Exception as e:
        return False, str(e)


def save_record(record_type, data, prediction):
    if st.session_state.auth_token:
        headers = {"Authorization": f"Bearer {st.session_state.auth_token}"}
        payload = {
            "record_type": record_type,
            "data": data,
            "prediction": prediction
        }
        try:
            requests.post(f"{BACKEND_URL}/records", json=payload, headers=headers)
        except:
            pass

# --- Main App Logic ---

# Auto-Login Check
if not st.session_state.auth_token:
    val = load_session()
    if val:
        st.session_state.auth_token = val.get("token")
        st.session_state.username = val.get("username")
        # Validate token by fetching profile
        fetch_profile()
        if not st.session_state.profile:
            # Token invalid
            st.session_state.auth_token = None
            st.session_state.username = None
            clear_session()

if not st.session_state.auth_token:
    # LOGIN / SIGNUP SCREEN
    if 'auth_mode' not in st.session_state:
        st.session_state.auth_mode = 'login'

    def toggle_auth_mode():
        st.session_state.auth_mode = 'signup' if st.session_state.auth_mode == 'login' else 'login'

    # Centered Container for Auth
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.session_state.auth_mode == 'login':
            st.markdown("<h1 style='text-align: center; color: #00d2ff; margin-bottom: 10px;'>AIO Healthcare System</h1>", unsafe_allow_html=True)
            st.markdown("<p style='text-align: center; color: #ccc; margin-bottom: 30px;'>Secure Login</p>", unsafe_allow_html=True)
            
            username = st.text_input("Username", key="login_user")
            password = st.text_input("Password", type="password", key="login_pass")
            
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("Login", use_container_width=True):
                if username and password:
                    token_data = login(username, password)
                    if token_data:
                        st.session_state.auth_token = token_data["access_token"]
                        st.session_state.username = username
                        fetch_profile() # Fetch profile on login
                        st.rerun()
                    else:
                        st.error("Invalid credentials")
                else:
                    st.warning("Please fill in all fields")
            
            st.markdown("<div style='text-align: center; margin-top: 20px; color: #888;'>New here? <a href='#' id='signup_link'>Create an account</a></div>", unsafe_allow_html=True)
            if st.button("Create Account", key="goto_signup"):
                toggle_auth_mode()
                st.rerun()

        else:
            st.markdown("<h1 style='text-align: center; color: #00d2ff; margin-bottom: 10px;'>Join AIO Healthcare System</h1>", unsafe_allow_html=True)
            st.markdown("<p style='text-align: center; color: #ccc; margin-bottom: 30px;'>Create your account</p>", unsafe_allow_html=True)
            
            new_user = st.text_input("Username", key="signup_user")
            new_pass = st.text_input("Password", type="password", key="signup_pass")
            
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("Sign Up", use_container_width=True):
                if new_user and new_pass:
                    success, error_msg = signup(new_user, new_pass)
                    if success:
                        st.success("Account created! Please login.")
                        st.session_state.auth_mode = 'login'
                        st.rerun()
                    else:
                        st.error(f"Signup Failed: {error_msg}")
                else:
                    st.warning("Please fill in all fields")
            
            st.markdown("<div style='text-align: center; margin-top: 20px; color: #888;'>Already have an account?</div>", unsafe_allow_html=True)
            if st.button("Back to Login", key="goto_login"):
                toggle_auth_mode()
                st.rerun()

else:
    # LOGGED IN VIEW
    if not st.session_state.profile:
        fetch_profile()

    # --- Sidebar ---
    with st.sidebar:
        # User Profile Picture
        p = st.session_state.profile
        if p.get('profile_picture'):
            st.markdown(f'<img src="data:image/png;base64,{p.get("profile_picture")}" class="profile-pic">', unsafe_allow_html=True)
        else:
             st.markdown(f'<div style="text-align:center; font-size:64px;">👤</div>', unsafe_allow_html=True)

        st.markdown(f"<h3 style='text-align: center; color: #00d2ff; margin-top: 10px;'>{st.session_state.username}</h3>", unsafe_allow_html=True)
        
        selected = option_menu(
            menu_title=None,
            options=['Profile', 'Diabetes Prediction', 'Heart Disease Prediction', 'Liver Disease Prediction', 'Healthcare Chatbot'],
            icons=['person', 'droplet-fill', 'heart-pulse', 'activity', 'robot'],
            default_index=0,
            styles={
                "container": {"padding": "0!important", "background-color": "transparent"},
                "icon": {"color": "#00d2ff", "font-size": "18px"}, 
                "nav-link": {"font-size": "16px", "text-align": "left", "margin":"5px", "--hover-color": "#262730"},
                "nav-link-selected": {"background-color": "#00d2ff"},
            }
        )
        
        if st.button("Logout"):
            clear_session()
            st.session_state.auth_token = None
            st.session_state.username = None
            st.session_state.profile = {}
            st.rerun()
            
        st.markdown("---")
        st.markdown("<div style='text-align: center; color: #888;'>AIO Healthcare System</div>", unsafe_allow_html=True)


    # --- User Profile Page ---
    if selected == 'Profile':
        st.title(f"User Profile")
        
        # Profile Data Manager
        p = st.session_state.profile
        
        with st.form("profile_form"):
            st.subheader("Personal Details")
            c1, c2 = st.columns(2)
            
            # Profile Photo
            c1.markdown("### Profile Photo")
            uploaded_file = c1.file_uploader("Upload Image", type=['png', 'jpg', 'jpeg'])
            img_b64 = p.get('profile_picture')
            if uploaded_file is not None:
                bytes_data = uploaded_file.getvalue()
                img_b64 = base64.b64encode(bytes_data).decode()
                c1.image(uploaded_file, width=150)
            elif img_b64:
                 c1.markdown(f'<img src="data:image/png;base64,{img_b64}" width="150" style="border-radius:10px;">', unsafe_allow_html=True)

            
            full_name = c2.text_input("Full Name", value=p.get('full_name') or "")
            email = c2.text_input("Email", value=p.get('email') or "")
            
            c3, c4 = st.columns(2)
            gender_opts = ["Male", "Female", "Other"]
            default_gender_idx = 0
            if p.get('gender') in gender_opts:
                default_gender_idx = gender_opts.index(p.get('gender'))
            gender = c3.selectbox("Gender", gender_opts, index=default_gender_idx)
            
            # Blood Type
            blood_opts = ["Unknown", "A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"]
            default_blood_idx = 0
            if p.get('blood_type') in blood_opts:
                default_blood_idx = blood_opts.index(p.get('blood_type'))
            blood_type = c4.selectbox("Blood Type", blood_opts, index=default_blood_idx)

            dob_val = pd.to_datetime(p.get('dob')) if p.get('dob') else pd.to_datetime("2000-01-01")
            dob = c3.date_input("Date of Birth", value=dob_val)
            
            height = c4.number_input("Height (cm)", value=float(p.get('height') or 170.0))
            weight = c3.number_input("Weight (kg)", value=float(p.get('weight') or 70.0))
            
            existing_ailments = st.text_area("Existing Ailments / Medical History", value=p.get('existing_ailments') or "", help="Allergies, chronic conditions, etc.")

            if st.form_submit_button("Save Profile"):
                update_data = {
                    "full_name": full_name,
                    "email": email,
                    "gender": gender,
                    "blood_type": blood_type,
                    "dob": str(dob),
                    "height": height,
                    "weight": weight,
                    "existing_ailments": existing_ailments,
                    "profile_picture": img_b64,
                    "allow_data_collection": p.get('allow_data_collection', True) # Default to True if missing
                }
                if update_profile(update_data):
                    st.success("Profile updated successfully!")
                    st.rerun()
                else:
                    st.error("Failed to update profile.")
            
            st.markdown("### Privacy Settings")
            allow_data = st.checkbox("Allow Data Collection & Chat History", value=p.get('allow_data_collection', True), help="If disabled, your chats will not be saved.")
            if allow_data != p.get('allow_data_collection', True):
                # Auto-save privacy toggle on change
                update_data={
                    "allow_data_collection": allow_data
                }
                if update_profile(update_data):
                    st.toast("Privacy settings updated.")
                    st.rerun()
            

        st.divider()
        st.subheader("Past Health Records")
        
        headers = {"Authorization": f"Bearer {st.session_state.auth_token}"}
        try:
            res = requests.get(f"{BACKEND_URL}/records", headers=headers)
            if res.status_code == 200:
                records = res.json()
                if records:
                    for rec in records:
                        # Clean Card Layout
                        with st.container():
                            st.markdown(f"""
                            <div style="background-color: rgba(255, 255, 255, 0.05); padding: 15px; border-radius: 10px; margin-bottom: 10px; border-left: 4px solid #00d2ff;">
                                <h4>{rec['record_type']}</h4>
                                <p style="font-size: 14px; color: #ccc;">Date: {rec['timestamp'].split('T')[0]}</p>
                                <p style="font-weight: bold; color: white;">Result: {rec['prediction']}</p>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            c_del, c_view = st.columns([1, 5])
                            with c_del:
                                if st.button("🗑️ Delete", key=f"del_{rec['id']}"):
                                    if delete_record(rec['id']):
                                        st.success("Record deleted.")
                                        st.rerun()
                                    else:
                                        st.error("Failed to delete.")
                                        
                            with st.expander("View Details"):
                                st.json(rec['data'])
                            st.markdown("<hr style='margin: 10px 0; border-color: #444;'>", unsafe_allow_html=True)

                else:
                    st.info("No records found.")
            else:
                st.error("Failed to fetch records.")
        except Exception as e:
            st.error(f"Connection error: {e}")

    # --- Diabetes Prediction Page ---
    if selected == 'Diabetes Prediction':
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.title('Diabetes Prediction')
            st.markdown("Enter the patient's details below to predict the likelihood of diabetes.")
        with col2:
            lottie_diabetes = load_lottieurl("https://assets5.lottiefiles.com/packages/lf20_iux66kzh.json")
            if lottie_diabetes:
                st_lottie(lottie_diabetes, height=150, key="diabetes_anim")

        # Auto-fill Logic
        p = st.session_state.profile
        default_age = 30.0
        if p.get('dob'):
             try:
                 dob_date = pd.to_datetime(p.get('dob'))
                 now = pd.to_datetime('today')
                 default_age = float((now - dob_date).days // 365)
             except: pass
        
        default_bmi = 25.0
        if p.get('height') and p.get('weight') and p.get('height') > 0:
            default_bmi = round(p.get('weight') / ((p.get('height')/100)**2), 1)

        gender_idx = 0
        if p.get('gender') == 'Male': gender_idx = 1
        elif p.get('gender') == 'Female': gender_idx = 0
        
        col1, col2, col3 = st.columns(3)
        with col1:
            gender = st.selectbox('Gender', ['Female', 'Male'], index=gender_idx)
            gender_val = 0.0 if gender == 'Female' else 1.0
            
            smoking_history = st.selectbox('Smoking History', ['never', 'No Info', 'current', 'former', 'ever', 'not current'])
            smoking_map = {'never': 0, 'No Info': 1, 'current': 2, 'former': 3, 'ever': 4, 'not current': 5}
            smoking_val = float(smoking_map[smoking_history])
            
            hypertension = st.selectbox('Hypertension', ['No', 'Yes'])
            hypertension_val = 1.0 if hypertension == 'Yes' else 0.0

        with col2:
            age = st.number_input('Age', min_value=0.0, max_value=120.0, step=1.0, value=default_age)
            bmi = st.number_input('BMI', min_value=0.0, max_value=100.0, step=0.1, value=default_bmi)
            heart_disease = st.selectbox('Heart Disease', ['No', 'Yes'])
            heart_disease_val = 1.0 if heart_disease == 'Yes' else 0.0

        with col3:
            hba1c_level = st.number_input('HbA1c Level', min_value=0.0, max_value=20.0, step=0.1)
            blood_glucose_level = st.number_input('Blood Glucose Level', min_value=0.0, max_value=500.0, step=1.0)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        if st.button('Analyze Risk'):
            if hba1c_level == 0.0 or blood_glucose_level == 0.0:
                st.warning("Please enter valid HbA1c and Blood Glucose levels (must be > 0).")
            else:
                with st.spinner('Analyzing health data...'):
                    if diabetes_model:
                        input_data = np.array([[gender_val, age, hypertension_val, heart_disease_val, smoking_val, bmi, hba1c_level, blood_glucose_level]], dtype=object)
                        input_data = input_data.astype(float)
                        diab_prediction = diabetes_model.predict(input_data)

                        prediction_text = ""
                        st.markdown("<div class='result-card'>", unsafe_allow_html=True)
                        if diab_prediction[0] == 1:
                            prediction_text = "High Risk"
                            st.error('### High Risk Detected')
                            st.write('The analysis suggests a high probability of diabetes. Please consult a specialist.')
                        else:
                            prediction_text = "Low Risk"
                            st.success('### Low Risk Detected')
                            st.write('The analysis suggests the patient is healthy. Maintain a healthy lifestyle!')
                        st.markdown("</div>", unsafe_allow_html=True)
                        
                        # Save to Backend
                        data_dict = {
                            "gender": gender, "age": age, "hypertension": hypertension, 
                            "heart_disease": heart_disease, "smoking": smoking_history, 
                            "bmi": bmi, "hba1c": hba1c_level, "glucose": blood_glucose_level
                        }
                        save_record("Diabetes", data_dict, prediction_text)
                    else:
                        st.error("Model not loaded.")


    # --- Heart Disease Prediction Page ---
    if selected == 'Heart Disease Prediction':
        col1, col2 = st.columns([2, 1])
        with col1:
            st.title('Heart Disease Prediction')
            st.markdown("Assess cardiovascular health using advanced machine learning models.")
        with col2:
            # Heart Animation - Beating Heart
            lottie_heart = load_lottieurl("https://assets8.lottiefiles.com/packages/lf20_wbj50s.json")
            if lottie_heart:
                st_lottie(lottie_heart, height=150, key="heart_anim")

        # Auto-fill Logic
        p = st.session_state.profile
        default_age = 30.0
        if p.get('dob'):
             try:
                 dob_date = pd.to_datetime(p.get('dob'))
                 now = pd.to_datetime('today')
                 default_age = float((now - dob_date).days // 365)
             except: pass
        
        gender_idx = 0 
        # Note: Heart model uses Female first, Male second in list usually? 
        # Check selectbox: ['Female', 'Male']
        if p.get('gender') == 'Male': gender_idx = 1
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            age = st.number_input('Age', min_value=0.0, step=1.0, value=default_age, key="heart_age")
            trestbps = st.number_input('Resting BP', min_value=0.0, step=1.0)
            restecg = st.number_input('Resting ECG', min_value=0.0, step=1.0)
            oldpeak = st.number_input('ST Depression', min_value=0.0, step=0.1)

        with col2:
            gender = st.selectbox('Gender', ['Female', 'Male'], index=gender_idx, key="heart_gender")
            gender_val = 1.0 if gender == 'Male' else 0.0
            chol = st.number_input('Cholesterol', min_value=0.0, step=1.0)
            thalach = st.number_input('Max Heart Rate', min_value=0.0, step=1.0)
            slope = st.number_input('ST Slope', min_value=0.0, step=1.0)

        with col3:
            cp = st.number_input('Chest Pain Type', min_value=0.0, step=1.0)
            fbs = st.number_input('Fasting BS > 120', min_value=0.0, step=1.0)
            exang = st.number_input('Exercise Angina', min_value=0.0, step=1.0)
            ca = st.number_input('Major Vessels', min_value=0.0, step=1.0)

        with col4:
            thal = st.selectbox('Thal', ['Normal', 'Fixed Defect', 'Reversible Defect'])
            thal_map = {'Normal': 0, 'Fixed Defect': 1, 'Reversible Defect': 2}
            thal_val = float(thal_map[thal])

        st.markdown("<br>", unsafe_allow_html=True)

        if st.button('Analyze Heart Health'):
            with st.spinner('Processing cardiovascular data...'):
                if heart_disease_model:
                    input_data = np.array([[age, gender_val, cp, trestbps, chol, fbs, restecg, thalach, exang, oldpeak, slope, ca, thal_val]], dtype=object)
                    input_data = input_data.astype(float)
                    heart_prediction = heart_disease_model.predict(input_data)

                    prediction_text = ""
                    st.markdown("<div class='result-card'>", unsafe_allow_html=True)
                    if heart_prediction[0] == 1:
                        prediction_text = "Heart Disease Detected"
                        st.error('### Heart Disease Detected')
                        st.write('The model predicts a presence of heart disease. Immediate medical attention is recommended.')
                    else:
                        prediction_text = "Healthy Heart"
                        st.success('### Healthy Heart')
                        st.write('The model predicts no heart disease. Keep up the good work!')
                    st.markdown("</div>", unsafe_allow_html=True)

                    # Save to Backend
                    data_dict = {
                        "age": age, "gender": gender, "cp": cp, "trestbps": trestbps, 
                        "chol": chol, "fbs": fbs, "restecg": restecg, "thalach": thalach,
                        "exang": exang, "oldpeak": oldpeak, "slope": slope, "ca": ca, "thal": thal
                    }
                    save_record("Heart Disease", data_dict, prediction_text)
                else:
                    st.error("Model not loaded.")


    # --- Liver Disease Prediction Page ---
    if selected == "Liver Disease Prediction":
        col1, col2 = st.columns([2, 1])
        with col1:
            st.title("Liver Disease Prediction")
            st.markdown("Early detection of liver conditions using biochemical markers.")
        with col2:
            # Updated Animation: Liver/Medical Analysis
            lottie_liver = load_lottieurl("https://assets5.lottiefiles.com/packages/lf20_x1ksszsd.json") # Medical Research/Analysis
            if lottie_liver:
                st_lottie(lottie_liver, height=150, key="liver_anim")

        # Auto-fill Logic
        p = st.session_state.profile
        default_age = 30.0
        if p.get('dob'):
             try:
                 dob_date = pd.to_datetime(p.get('dob'))
                 now = pd.to_datetime('today')
                 default_age = float((now - dob_date).days // 365)
             except: pass
        
        gender_idx = 0
        if p.get('gender') == 'Male': gender_idx = 1
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            age = st.number_input('Age', min_value=0.0, step=1.0, value=default_age, key="liver_age")
            alkaline_phosphotase = st.number_input('Alkaline Phosphotase', min_value=0.0, step=1.0)
        
        with col2:
            gender = st.selectbox('Gender', ['Female', 'Male'], index=gender_idx, key="liver_gender")
            gender_val = 1.0 if gender == 'Male' else 0.0 
            alamine_aminotransferase = st.number_input('Alamine Aminotransferase', min_value=0.0, step=1.0)

        with col3:
            total_bilirubin = st.number_input('Total Bilirubin', min_value=0.0, step=0.1)
            albumin_globulin_ratio = st.number_input('Albumin/Globulin Ratio', min_value=0.0, step=0.1)
        
        st.markdown("<br>", unsafe_allow_html=True)

        if st.button("Analyze Liver Function"):
            with st.spinner('Analyzing liver enzymes...'):
                if liver_model:
                    def preprocess_input(data):
                        skewed = ['Total_Bilirubin', 'Alkaline_Phosphotase', 'Alamine_Aminotransferase','Albumin_and_Globulin_Ratio']
                        data[skewed] = np.log1p(data[skewed])
                        attributes = [col for col in data.columns]
                        data[attributes] = scaler.transform(data[attributes])
                        return data
                    
                    input_data = [age, gender_val, total_bilirubin, alkaline_phosphotase, alamine_aminotransferase, albumin_globulin_ratio]  
                    column_names = ['Age', 'Gender', 'Total_Bilirubin', 'Alkaline_Phosphotase','Alamine_Aminotransferase', 'Albumin_and_Globulin_Ratio']
                    user_data = pd.DataFrame([input_data], columns=column_names)
                    user_data[column_names] = user_data[column_names].apply(pd.to_numeric, errors='coerce')
                    
                    preprocessed_data = preprocess_input(user_data)
                    prediction = liver_model.predict(preprocessed_data)                  
                    
                    prediction_text = ""
                    st.markdown("<div class='result-card'>", unsafe_allow_html=True)
                    if prediction[0] == 0:
                        prediction_text = "Healthy Liver"
                        st.success("### Healthy Liver")
                        st.write("The analysis indicates normal liver function.")
                    else:
                        prediction_text = "Liver Disease Detected"
                        st.error("### Liver Disease Detected")
                        st.write("The analysis indicates potential liver disease. Please consult a doctor.")
                    st.markdown("</div>", unsafe_allow_html=True)

                    # Save to Backend
                    data_dict = {
                        "age": age, "gender": gender, "total_bilirubin": total_bilirubin,
                        "alkaline_phosphotase": alkaline_phosphotase, "alamine_aminotransferase": alamine_aminotransferase,
                        "albumin_globulin_ratio": albumin_globulin_ratio
                    }
                    save_record("Liver Disease", data_dict, prediction_text)
                else:
                    st.error("Model not loaded.")


    # --- Chatbot Page ---
    if selected == 'Healthcare Chatbot':
        col1, col2 = st.columns([2, 1])
        with col1:
            st.title("AIO Healthcare System")
            st.markdown("Ask me anything about your health concerns. I can recall your recent test results.")
        with col2:
            lottie_bot = load_lottieurl("https://assets3.lottiefiles.com/packages/lf20_ofa3xwo7.json")
            if lottie_bot:
                st_lottie(lottie_bot, height=150, key="bot_anim")

        # Initialize or Load chat history from Backend
        if "messages" not in st.session_state or not st.session_state.messages:
            headers = {"Authorization": f"Bearer {st.session_state.auth_token}"}
            try:
                res = requests.get(f"{BACKEND_URL}/chat/history", headers=headers)
                if res.status_code == 200:
                    st.session_state.messages = res.json()
                else:
                    st.session_state.messages = []
            except Exception as e:
                st.session_state.messages = []

        # Prepare User Avatar
        user_avatar = "👤" # Default
        if st.session_state.profile and st.session_state.profile.get("profile_picture"):
            try:
                import base64
                from PIL import Image
                import io
                
                # Handle data:image/png;base64,... header if present
                b64_str = st.session_state.profile["profile_picture"]
                if "," in b64_str:
                    b64_str = b64_str.split(",")[1]
                    
                image_data = base64.b64decode(b64_str)
                user_avatar = Image.open(io.BytesIO(image_data))
            except Exception as e:
                pass

        # Display chat messages from history on app rerun
        for message in st.session_state.messages:
            avatar_to_use = user_avatar if message["role"] == "user" else "🤖"
            with st.chat_message(message["role"], avatar=avatar_to_use):
                st.markdown(message["content"])

        # React to user input
        if prompt := st.chat_input("What is your health concern?"):
            # Display user message in chat message container
            with st.chat_message("user", avatar=user_avatar):
                st.markdown(prompt)
            # Add user message to chat history
            st.session_state.messages.append({"role": "user", "content": prompt})
            
            # Prepare headers and payload
            headers = {"Authorization": f"Bearer {st.session_state.auth_token}"}
            payload = {
                "message": prompt,
                "history": st.session_state.messages[:-1] # Send all history EXCEPT the prompt we just added
            }
            
            with st.chat_message("assistant", avatar="🤖"):
                with st.spinner("Thinking..."):
                    try:
                        res = requests.post(f"{BACKEND_URL}/chat", json=payload, headers=headers)
                        if res.status_code == 200:
                            response_text = res.json()["response"]
                            st.markdown(response_text)
                            st.session_state.messages.append({"role": "assistant", "content": response_text})
                        else:
                            st.error("Error communicating with AI.")
                    except Exception as e:
                        st.error(f"Connection error: {e}")
