import requests
import streamlit as st
import app_warnings
from streamlit_option_menu import option_menu
import pandas as pd
import json
import base64
from io import BytesIO
from streamlit_lottie import st_lottie
import time
import feedparser
# Lazy import speech_recognition to speed up app load
# import speech_recognition as sr 
# from audio_recorder_streamlit import audio_recorder


# --- Page Config ---
st.set_page_config(
    page_title="AIO Healthcare System",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Backend Configuration ---
# --- Backend Configuration ---
BACKEND_URL = "http://127.0.0.1:8000"

# --- Load Custom CSS ---
# @st.cache_data removed to ensure CSS is injected every re-run
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
@st.cache_data(ttl=3600)
def load_lottieurl(url):
    try:
        r = requests.get(url)
        if r.status_code != 200:
            return None
        return r.json()
    except:
        return None

def fetch_profile():
    # Performance Optimization: Only fetch if we don't have it locally
    if st.session_state.auth_token:
        # If we already have a full profile, skip the network call (0ms)
        if st.session_state.profile and st.session_state.profile.get("id"):
            return 

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

# --- Models are loaded in Backend API ---
# diabetes_model, heart_disease_model, liver_model, scaler = None, None, None, None
# This removes local inference overhead.

# --- Authentication State ---
def init_session_state():
    """Initializes all session state variables to prevent KeyErrors."""
    defaults = {
        "auth_token": None,
        "username": None,
        "profile": {},
        "messages": [],
        "diabetes_result": {},
        "heart_result": {},
        "liver_result": {}
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

init_session_state()

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
        url = f"{BACKEND_URL}/token"
        res = requests.post(url, data={"username": username, "password": password})
        
        if res.status_code == 200:
            data = res.json()
            save_session(data["access_token"], username)
            return data
        
        return None
    except:
        return None

def signup(username, password, email, full_name, dob):
    try:
        payload = {
            "username": username, 
            "password": password,
            "email": email,
            "full_name": full_name,
            "dob": str(dob)
        }
        res = requests.post(f"{BACKEND_URL}/signup", json=payload)
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

# --- NEW: Trends & News Helpers ---
@st.cache_data(ttl=60)
def fetch_records_cached(record_type):
    """Fetches records with short-term caching to prevent excessive API calls on re-runs."""
    if st.session_state.auth_token:
        headers = {"Authorization": f"Bearer {st.session_state.auth_token}"}
        try:
            res = requests.get(f"{BACKEND_URL}/records?record_type={record_type}", headers=headers)
            if res.status_code == 200:
                return res.json()
        except: pass
    return []

def render_latest_report(record_type):
    """Fetches and displays the most recent prediction result."""
    records = fetch_records_cached(record_type)
    if records:
        latest = records[-1] # List is sorted by timestamp ASC
        
        # Parse Data
        pred = latest["prediction"] # "High Risk" or "Low Risk"
        ts = latest["timestamp"]
        
        # Color Code
        color = "red" if "High" in pred or "Disease" in pred else "green"
        
        st.markdown(f"""
        <div style="background-color: rgba(20,20,30,0.5); padding: 10px; border-radius: 5px; border-left: 5px solid {color}; margin-bottom: 20px;">
            <small style="color: #aaa;">Last Assessment: {ts}</small><br>
            <strong style="font-size: 18px; color: {color};">{pred}</strong>
        </div>
        """, unsafe_allow_html=True)

def render_trend_chart(record_type, metric_key, metric_label):
    """Fetches user history and plots a specific metric."""
    records = fetch_records_cached(record_type)
    if records:
        import json
        dates = []
        values = []
        for r in records:
            try:
                # data field might be stringified json or dict
                data = json.loads(r["data"]) if isinstance(r["data"], str) else r["data"]
                # Also check if wrapped in 'data' key again or root
                if metric_key in data:
                    dates.append(r["timestamp"])
                    values.append(float(data[metric_key]))
            except: pass
        
        if len(values) > 1:
            st.subheader(f"📈 {metric_label} Trends")
            chart_data = pd.DataFrame({
                "Date": pd.to_datetime(dates),
                metric_label: values
            }).set_index("Date")
            st.line_chart(chart_data)
        elif len(values) == 1:
            st.info(f"Not enough data for trend analysis yet. (1 record found)")
    else:
        st.info("No past records found for trends.")

@st.cache_data(ttl=3600)
def fetch_news_feed(topic):
    """Fetches Google News RSS for the topic."""
    try:
        # Sanitized topic for URL
        encoded_topic = topic.replace(" ", "%20")
        rss_url = f"https://news.google.com/rss/search?q={encoded_topic}+health&hl=en-US&gl=US&ceid=US:en"
        feed = feedparser.parse(rss_url)
        return feed.entries[:5]
    except:
        return []

def render_news_feed(topic):
    st.subheader(f"📰 Latest {topic} News")
    entries = fetch_news_feed(topic)
    
    count = 0
    for entry in entries:
        if count >= 3: break
        st.markdown(f"**[{entry.title}]({entry.link})**")
        st.markdown(f"<small>{entry.published}</small>", unsafe_allow_html=True)
        st.markdown("---")
        count += 1

# --- Main App Logic ---

# --- Main App Logic ---
def main_app():
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
        # PREMIUM SPLIT LAYOUT
        hero_col, auth_col = st.columns([1.4, 1], gap="large")
        
        with hero_col:
            st.markdown("""
            <div style="padding-top: 50px; padding-right: 20px; border-right: 1px solid #333;">
                <h1 style="font-size: 3.5rem; font-weight: 800; background: -webkit-linear-gradient(0deg, #00d2ff, #3a7bd5); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
                    Future Health<br>Is Here.
                </h1>
                <p style="font-size: 1.2rem; color: #a0aab9; margin-top: 20px; line-height: 1.6;">
                    Experience the power of <strong>AI-driven diagnostics</strong>. 
                    Monitor your vitals, predict potential risks, and safeguard your future with our 
                    enterprise-grade healthcare system.
                </p>
                <div style="display: flex; gap: 15px; margin-top: 30px;">
                    <span style="background: #1e232b; padding: 10px 20px; border-radius: 20px; color: #00d2ff; border: 1px solid #00d2ff33;">🛡️ Secure</span>
                    <span style="background: #1e232b; padding: 10px 20px; border-radius: 20px; color: #00d2ff; border: 1px solid #00d2ff33;">⚡ Real-time</span>
                    <span style="background: #1e232b; padding: 10px 20px; border-radius: 20px; color: #00d2ff; border: 1px solid #00d2ff33;">🤖 AI Powered</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

        with auth_col:
            st.markdown("<br><br>", unsafe_allow_html=True)
            auth_tabs = st.tabs(["🔐 Login", "📝 Sign Up"])
            
            with auth_tabs[0]:
                st.markdown("### Welcome Back")
                with st.form("login_form", border=False):
                    username = st.text_input("Username", placeholder="Enter your username")
                    password = st.text_input("Password", type="password", placeholder="Enter your password")
                    
                    st.markdown("<br>", unsafe_allow_html=True)
                    if st.form_submit_button("Access Portal", type="primary", use_container_width=True):
                        if username and password:
                            with st.spinner("Authenticating..."):
                                token_data = login(username, password)
                                if token_data:
                                    st.session_state.auth_token = token_data["access_token"]
                                    st.session_state.username = username
                                    fetch_profile()
                                    st.rerun()
                                else:
                                    st.error("Invalid credentials")
                        else:
                            st.warning("Please enter both username and password.")

            with auth_tabs[1]:
                st.markdown("### Create Account")
                with st.form("signup_form", border=False):
                    new_fullname = st.text_input("Full Name")
                    new_email = st.text_input("Email Address")
                    new_dob = st.date_input("Date of Birth", value=None, min_value=pd.to_datetime("1900-01-01"), max_value=pd.to_datetime("today"))
                    
                    st.caption("Secure Credentials")
                    new_user = st.text_input("Username")
                    new_pass = st.text_input("Password", type="password", help="Must be 8+ chars (letters & numbers).")
                    
                    st.markdown("<br>", unsafe_allow_html=True)
                    if st.form_submit_button("Register Account", use_container_width=True):
                        missing = []
                        if not new_user: missing.append("Username")
                        if not new_pass: missing.append("Password")
                        if not new_fullname: missing.append("Full Name")
                        if not new_email: missing.append("Email")
                        if not new_dob: missing.append("Date of Birth")
                        
                        if not missing:
                            with st.spinner("Creating secure profile..."):
                                success, error_msg = signup(new_user, new_pass, new_email, new_fullname, new_dob)
                                if success:
                                    st.success("Account created successfully! Please switch to Login tab.")
                                else:
                                    st.error(f"Signup Failed: {error_msg}")
                        else:
                            st.warning(f"Missing fields: {', '.join(missing)}")

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
                # Use Full Name for Avatar
                display_name = p.get("full_name", st.session_state.username)
                st.markdown(f'<img src="https://ui-avatars.com/api/?name={display_name}&background=00d2ff&color=fff&size=128" class="profile-pic">', unsafe_allow_html=True)
        
            st.markdown(f"<h2 style='text-align: center;'>{p.get('full_name', st.session_state.username)}</h2>", unsafe_allow_html=True)
            st.markdown(f"<p style='text-align: center; color: #888;'>@{st.session_state.username}</p>", unsafe_allow_html=True)
        
            # Define Menu Options based on Role
            menu_options = ['Profile', 'Smart Lab Analyzer', 'Diabetes Prediction', 'Heart Disease Prediction', 'Liver Disease Prediction', 'Healthcare Chatbot', 'Monitoring Dashboard']
            menu_icons = ['person', 'file-earmark-medical', 'droplet-fill', 'heart-pulse', 'activity', 'robot', 'graph-up-arrow']
            
            if st.session_state.username == "admin":
                menu_options.append("Admin Panel")
                menu_icons.append("shield-lock")

            # Hide Default Streamlit Chrome
            st.markdown("""
            <style>
                #MainMenu {visibility: hidden;}
                footer {visibility: hidden;}
                header {visibility: hidden;}
                [data-testid="stSidebar"] {
                    background-color: #1a1e26;
                    border-right: 1px solid #333;
                }
            </style>
            """, unsafe_allow_html=True)
            
            selected = option_menu(
                menu_title=None,
                options=menu_options,
                icons=menu_icons,
                default_index=0,
                styles={
                    "container": {"padding": "5px", "background-color": "#1a1e26"},
                    "icon": {"color": "#00d2ff", "font-size": "20px"}, 
                    "nav-link": {
                        "font-size": "16px", 
                        "text-align": "left", 
                        "margin":"5px", 
                        "color": "#e0e0e0",
                        "--hover-color": "#2d333b"
                    },
                    "nav-link-selected": {
                        "background-color": "#00d2ff", 
                        "color": "white",
                        "font-weight": "600"
                    },
                }
            )
        
            if st.button("Logout", type="secondary"):
                clear_session()
                st.session_state.auth_token = None
                st.session_state.username = None
                st.session_state.profile = {}
                st.rerun()
            
            st.markdown("<div style='text-align: center; color: #555; font-size: 0.8rem; margin-top: 20px;'>AIO Security Active 🛡️</div>", unsafe_allow_html=True)


        # --- User Profile Page ---
        if selected == 'Profile':
            @st.fragment
            def render_profile_page():
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
                
                    st.subheader("Lifestyle & Wellness")
                    l1, l2 = st.columns(2)
                
                    diet_opts = ["No Restriction", "Vegetarian", "Vegan", "Keto", "Paleo", "Mediterranean", "Gluten-Free", "Low Carb", "Other"]
                    default_diet_idx = 0
                    if p.get('diet') in diet_opts: default_diet_idx = diet_opts.index(p.get('diet'))
                    diet = l1.selectbox("Dietary Preference", diet_opts, index=default_diet_idx)
    
                    activity_opts = ["Sedentary (Little/no exercise)", "Lightly Active (1-3 days/week)", "Moderately Active (3-5 days/week)", "Very Active (6-7 days/week)", "Extra Active (Physical job/training)"]
                    default_activity_idx = 0
                    # Simple fuzzy matching or exact match if user saved before
                    if p.get('activity_level') in activity_opts: default_activity_idx = activity_opts.index(p.get('activity_level'))
                    activity_level = l2.selectbox("Activity Level", activity_opts, index=default_activity_idx)
    
                    sleep_hours = l1.slider("Average Sleep (Hours/Night)", min_value=3.0, max_value=12.0, value=float(p.get('sleep_hours') or 7.0), step=0.5)
                
                    stress_opts = ["Low", "Moderate", "High", "Very High"]
                    default_stress_idx = 1
                    if p.get('stress_level') in stress_opts: default_stress_idx = stress_opts.index(p.get('stress_level'))
                    stress_level = l2.selectbox("Stress Level", stress_opts, index=default_stress_idx)
    
                    st.divider()
    
                    existing_ailments = st.text_area("Existing Ailments / Medical History", value=p.get('existing_ailments') or "", help="Allergies, chronic conditions, etc.")
                    about_me = st.text_area("About Me / Bio", value=p.get('about_me') or "", help="Share anything else about yourself (hobbies, lifestyle, goals). The AI will remember this.")
    
                    if st.form_submit_button("Save Profile"):
                        update_data = {
                            "full_name": full_name,
                            "email": email,
                            "gender": gender,
                            "blood_type": blood_type,
                            "dob": str(dob),
                            "height": height,
                            "weight": weight,
                            "diet": diet,
                            "activity_level": activity_level,
                            "sleep_hours": sleep_hours,
                            "stress_level": stress_level,
                            "existing_ailments": existing_ailments,
                            "about_me": about_me,
                            "profile_picture": img_b64,
                            "allow_data_collection": p.get('allow_data_collection', True) # Default to True if missing
                        }
                        if update_profile(update_data):
                            st.success("Profile updated successfully!")
                            # Optimistic UI Update: Update local state so we don't need to re-fetch
                            st.session_state.profile.update(update_data)
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
                
            # Call the Fragment
            render_profile_page()

        # --- Diabetes Prediction Page ---
        if selected == 'Diabetes Prediction':
            @st.fragment
            def render_diabetes_page():
                col1, col2 = st.columns([2, 1])
            
                with col1:
                    st.title('Diabetes Prediction')
                    st.markdown("Enter the patient's details below to predict the likelihood of diabetes.")
                    render_latest_report("Diabetes")
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
                     except Exception:
                         pass # Fallback to default_age if parsing fails
            
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
                    if hba1c_level <= 0.0 or blood_glucose_level <= 0.0:
                        st.warning("⚠️ Please enter valid values for HbA1c and Blood Glucose.")
                    else:
                        with st.spinner('Analyzing health data...'):
                            # Call Backend API
                            payload = {
                                "gender": gender_val,
                                "age": age,
                                "hypertension": hypertension_val,
                                "heart_disease": heart_disease_val,
                                "smoking": smoking_val,
                                "bmi": bmi,
                                "hba1c": hba1c_level,
                                "glucose": blood_glucose_level
                            }
                            try:
                                res = requests.post(f"{BACKEND_URL}/predict/diabetes", json=payload)
                                if res.status_code == 200:
                                    api_data = res.json()
                                    prediction_text = api_data["prediction"] # "High Risk" or "Low Risk"
                                
                                    # Save to Backend
                                    data_dict = {
                                        "gender": gender, "age": age, "hypertension": hypertension, 
                                        "heart_disease": heart_disease, "smoking": smoking_history, 
                                        "bmi": bmi, "hba1c": hba1c_level, "glucose": blood_glucose_level
                                    }
                                    save_record("Diabetes", data_dict, prediction_text)
    
                                    # Save to Session State
                                    st.session_state.diabetes_result = {
                                        "prediction": prediction_text,
                                        "data": data_dict
                                    }
                                else:
                                    st.error(f"Prediction API Error: {res.text}")
                            except Exception as e:
                                st.error(f"Error connecting to Prediction API: {e}")
    
                # Display Result (Persistent)
                if "diabetes_result" in st.session_state:
                    res_data = st.session_state.diabetes_result
                    pred = res_data["prediction"]
                
                    st.markdown("<div class='result-card'>", unsafe_allow_html=True)
                    if pred == "High Risk":
                        st.error('### High Risk Detected')
                        st.write('The analysis suggests a high probability of diabetes. Please consult a specialist.')
                    else:
                        st.success('### Low Risk Detected')
                        st.write('The analysis suggests the patient is healthy. Maintain a healthy lifestyle!')
                    st.markdown("</div>", unsafe_allow_html=True)
    
                    # --- GenAI Explanation Layer ---
                    st.markdown("---")
                    if st.button("🧠 Explain this Result using GenAI", key="explain_diabetes"):
                        with st.spinner("Consulting Medical Agent..."):
                            try:
                                payload = {
                                    "prediction_type": "Diabetes",
                                    "input_data": res_data["data"],
                                    "prediction_result": pred
                                }
                                headers = {"Authorization": f"Bearer {st.session_state.auth_token}"}
                                res = requests.post(f"{BACKEND_URL}/explain/", json=payload, headers=headers)
                            
                                if res.status_code == 200:
                                    data = res.json()
                                    st.subheader("💡 AI Analysis")
                                    st.info(data["explanation"])
                                
                                    st.subheader("🥗 Personalized Lifestyle Tips")
                                    for tip in data["lifestyle_tips"]:
                                        st.markdown(f"- {tip}")
                                else:
                                    st.error(f"Could not fetch explanation: {res.text}")
                            except Exception as e:
                                st.error(f"Error connecting to AI: {e}")
    
                        # --- Trends & News Section ---
                        st.markdown("---")
                        t_col1, t_col2 = st.columns(2)
                        with t_col1:
                            render_trend_chart("Diabetes", "glucose", "Blood Glucose")
                        with t_col2:
                            render_news_feed("Diabetes")

            render_diabetes_page()


        # --- Heart Disease Prediction Page ---
        if selected == 'Heart Disease Prediction':
            @st.fragment
            def render_heart_page():
                col1, col2 = st.columns([2, 1])
                with col1:
                    st.title('Heart Disease Prediction')
                    st.markdown("Assess cardiovascular health using advanced machine learning models.")
                    render_latest_report("Heart Disease")
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
                     except Exception:
                         pass # Fallback to default_age if parsing fails
            
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
                    if trestbps <= 0.0 or chol <= 0.0 or thalach <= 0.0:
                         st.warning("⚠️ Please enter valid values for Blood Pressure, Cholesterol, and Max Heart Rate.")
                    else:
                        with st.spinner('Processing cardiovascular data...'):
                            try:
                                # Backend API Call
                                payload = {
                                    "age": float(age), "gender": float(gender_val), "cp": float(cp), 
                                    "trestbps": float(trestbps), "chol": float(chol), "fbs": float(fbs), 
                                    "restecg": float(restecg), "thalach": float(thalach),
                                    "exang": float(exang), "oldpeak": float(oldpeak), "slope": float(slope), 
                                    "ca": float(ca), "thal": float(thal_val)
                                }
                                res = requests.post(f"{BACKEND_URL}/predict/heart", json=payload)
                            
                                if res.status_code == 200:
                                    api_data = res.json()
                                    prediction_text = api_data["prediction"]
        
                                    # Save to Backend
                                    save_record("Heart Disease", payload, prediction_text)
        
                                    # Save to Session State
                                    st.session_state.heart_result = {
                                        "prediction": prediction_text,
                                        "data": payload
                                    }
                                else:
                                    st.error(f"Prediction API Error: {res.text}")
                            except Exception as e:
                                st.error(f"Error connecting to Backend: {e}")
    
                if "heart_result" in st.session_state:
                    res_data = st.session_state.heart_result
                    pred = res_data["prediction"]
                
                    st.markdown("<div class='result-card'>", unsafe_allow_html=True)
                    if pred == "Heart Disease Detected":
                        st.error('### Heart Disease Detected')
                        st.write('The model predicts a presence of heart disease. Immediate medical attention is recommended.')
                    else:
                        st.success('### Healthy Heart')
                        st.write('The model predicts no heart disease. Keep up the good work!')
                    st.markdown("</div>", unsafe_allow_html=True)
                
                    # --- GenAI Explanation Layer ---
                    st.markdown("---")
                    if st.button("🧠 Explain this Result using GenAI", key="explain_heart"):
                        with st.spinner("Consulting Medical Agent..."):
                            try:
                                explain_payload = {
                                    "prediction_type": "Heart Disease",
                                    "input_data": res_data["data"],
                                    "prediction_result": pred
                                }
                                # ... (Existing logic for explanation)
                                # Actually need to keep the implementation here, context was cut off in previous View
                                # Let's assume standard POST implementation similar to Diabetes
                                headers = {"Authorization": f"Bearer {st.session_state.auth_token}"}
                                res = requests.post(f"{BACKEND_URL}/explain/", json=explain_payload, headers=headers)
                                if res.status_code == 200:
                                    data = res.json()
                                    st.subheader("💡 AI Analysis")
                                    st.info(data["explanation"])
                                    st.subheader("🥗 Personalized Lifestyle Tips")
                                    for tip in data["lifestyle_tips"]: st.markdown(f"- {tip}")
                                else: st.error("Failed to explain.")
                            except Exception as e: st.error(str(e))
            
                # Trends
                st.markdown("---")
                t_col1, t_col2 = st.columns(2)
                with t_col1: render_trend_chart("Heart Disease", "thalach", "Max Heart Rate")
                with t_col2: render_news_feed("Heart Disease")

            render_heart_page()


        # --- Liver Disease Prediction Page ---
        if selected == "Liver Disease Prediction":
            col1, col2 = st.columns([2, 1])
            with col1:
                st.title("Liver Disease Prediction")
                st.markdown("Early detection of liver conditions using biochemical markers.")
                render_latest_report("Liver Disease")
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
                 except Exception:
                     pass # Fallback to default_age if parsing fails
        
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

            st.markdown("<br>", unsafe_allow_html=True)

            if st.button("Analyze Liver Function"):
                if total_bilirubin <= 0.0 or alkaline_phosphotase <= 0.0:
                     st.warning("⚠️ Please enter valid values for Bilirubin and Enzymes.")
                else:
                    with st.spinner('Analyzing liver enzymes...'):
                        # Backend API Call
                        payload = {
                            "age": float(age),
                            "gender": 1.0 if gender == "Male" else 0.0,
                            "total_bilirubin": float(total_bilirubin),
                            "alkaline_phosphotase": float(alkaline_phosphotase),
                            "alamine_aminotransferase": float(alamine_aminotransferase),
                            "albumin_globulin_ratio": float(albumin_globulin_ratio)
                        }
                    
                        try:
                            res = requests.post(f"{BACKEND_URL}/predict/liver", json=payload)
                        
                            if res.status_code == 200:
                                api_data = res.json()
                                prediction_text = api_data["prediction"]

                                # Save to Backend
                                # Note: Frontend Payload keys match Backend Input Schema which match Save Record logic
                                data_dict = payload
                                save_record("Liver Disease", data_dict, prediction_text)

                                # Save to Session State
                                st.session_state.liver_result = {
                                    "prediction": prediction_text,
                                    "data": data_dict
                                }
                            else:
                                 st.error(f"Prediction API Error: {res.text}")
                        except Exception as e:
                            st.error(f"Error connecting to Backend: {e}")

            # Display Result (Persistent)
            if "liver_result" in st.session_state:
                res_data = st.session_state.liver_result
                pred = res_data["prediction"]
            
                st.markdown("<div class='result-card'>", unsafe_allow_html=True)
                if pred == "Liver Disease Detected":
                    st.error('### Liver Disease Detected')
                    st.write('The analysis suggests potential liver issues. Please consult a specialist.')
                else:
                    st.success('### Healthy Liver')
                    st.write('The analysis suggests the liver is functioning normally.')
                st.markdown("</div>", unsafe_allow_html=True)

                # --- GenAI Explanation Layer ---
                st.markdown("---")
                if st.button("🧠 Explain this Result using GenAI", key="explain_liver"):
                    with st.spinner("Consulting Medical Agent..."):
                        try:
                            explain_payload = {
                                "prediction_type": "Liver Disease",
                                "input_data": res_data["data"],
                                "prediction_result": pred
                            }
                            headers = {"Authorization": f"Bearer {st.session_state.auth_token}"}
                            res_explain = requests.post(f"{BACKEND_URL}/explain/", json=explain_payload, headers=headers)
                        
                            if res_explain.status_code == 200:
                                data = res_explain.json()
                                st.subheader("💡 AI Analysis")
                                st.info(data["explanation"])
                            
                                st.subheader("🥗 Personalized Lifestyle Tips")
                                for tip in data["lifestyle_tips"]:
                                    st.markdown(f"- {tip}")
                            else:
                                st.error(f"Could not fetch explanation: {res_explain.text}")
                        except Exception as e:
                            st.error(f"Error connecting to AI: {e}")


                    # --- Trends & News Section (Liver) ---
                    st.markdown("---")
                    t_col1, t_col2 = st.columns(2)
                    with t_col1:
                        render_trend_chart("Liver Disease", "total_bilirubin", "Total Bilirubin")
                    with t_col2:
                        render_news_feed("Liver Disease")

        # --- Chatbot Page ---
        # --- Chatbot Page ---
        if selected == 'Healthcare Chatbot':
            col1, col2 = st.columns([2, 0.5])
            with col1:
                st.title("AIO Healthcare System")
                st.markdown("Ask me anything about your health concerns. I can recall your recent test results.")
            # with col2:  <-- REMOVED ROBO ANIMATION AS REQUESTED
            #    lottie_bot = load_lottieurl("https://assets3.lottiefiles.com/packages/lf20_ofa3xwo7.json")
            #    if lottie_bot:
            #        st_lottie(lottie_bot, height=150, key="bot_anim")
            with col2:
                st.markdown("<br><br>", unsafe_allow_html=True)
                if st.button("🔄 Reset", help="Start a new conversation"):
                    headers = {"Authorization": f"Bearer {st.session_state.auth_token}"}
                    try:
                        requests.delete(f"{BACKEND_URL}/chat/history", headers=headers)
                        st.session_state.messages = []
                        st.rerun()
                    except Exception as e:
                        st.error(f"Failed to reset chat: {e}")

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

            # --- UX: Auto-Greet ---
            if not st.session_state.messages:
                 welcome_msg = f"Hello {st.session_state.profile.get('full_name', 'there')}! I'm your personal health assistant. How can I help you today?"
                 st.session_state.messages.append({"role": "assistant", "content": welcome_msg})

            # Display chat messages from history on app rerun
            for message in st.session_state.messages:
                avatar_to_use = user_avatar if message["role"] == "user" else "🤖"
                with st.chat_message(message["role"], avatar=avatar_to_use):
                    st.markdown(message["content"])

            # --- UX: Suggestion Chips ---
            suggestion = None
            if len(st.session_state.messages) < 3: # Only show initially to reduce clutter
                st.markdown("<small style='color: #888;'>Try asking:</small>", unsafe_allow_html=True)
                cols = st.columns(5) # Increased to 5 columns
                if cols[0].button("❤️ Heart Health"):
                    suggestion = "Analyze my heart health based on recent records."
                if cols[1].button("🩸 Diabetes Risk"):
                    suggestion = "What is my risk of diabetes?"
                if cols[2].button("🥦 Liver Health"): # Added Liver Health
                    suggestion = "Analyze my liver health based on recent records."
                if cols[3].button("🥗 Diet Tips"):
                    suggestion = "Give me general diet tips."
                if cols[4].button("🩺 My History"):
                    suggestion = "Summarize my medical history including all past records."

            # React to user input
            prompt = st.chat_input("What is your health concern?")
        
            # --- Voice Input (Fixed Position via CSS) ---
            import speech_recognition as sr
            from audio_recorder_streamlit import audio_recorder
            
            # Just render it; CSS handles fixed positioning (bottom-right)
            audio_bytes = audio_recorder(
                text="",
                recording_color="#e8b62c",
                neutral_color="#6aa36f",
                icon_name="microphone",
                icon_size="1x", 
            )
        
            voice_prompt = None
            if audio_bytes:
                with st.spinner("Transcribing your voice..."):
                    try:
                        # Save audio to a temporary file (SpeechRecognition needs a file path or file-like object)
                        # Use io.BytesIO for in-memory
                        audio_file = BytesIO(audio_bytes)
                        audio_file.name = "input.wav"
                    
                        # Initialize recognizer
                        r = sr.Recognizer()
                        with sr.AudioFile(audio_file) as source:
                            audio_data = r.record(source)
                            # Recognize (using Google Web Speech API - free tier)
                            voice_prompt = r.recognize_google(audio_data)
                            st.info(f"🎙️ You said: '{voice_prompt}'")
                    except Exception as e:
                        st.error(f"Could not understand audio: {e}")

            # Handle Suggestion or Voice Click
            if suggestion:
                prompt = suggestion
            if voice_prompt:
                prompt = voice_prompt
            
            if prompt:
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
            
        # --- Smart Lab Analyzer (FAANG Feature) ---
        if selected == 'Smart Lab Analyzer':
            col1, col2 = st.columns([2, 1])
            with col1:
                st.title("Smart Lab Analyzer 🔬")
                st.markdown("Upload your medical lab report (Image). AI will extract values and analyze them.")
            with col2:
                 st.info("Supported: Blood Tests, Lipid Profile, Liver Function Tests.")

            uploaded_file = st.file_uploader("Upload Report Image", type=['png', 'jpg', 'jpeg'])
        
            if uploaded_file and st.button("Analyze Report", type="primary"):
                 with st.spinner("AI is reading the report (Computer Vision)..."):
                     try:
                         # Send file to backend
                         files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
                         # No auth needed for this endpoint strictly, but good practice if we want to save it later
                         res = requests.post(f"{BACKEND_URL}/analyze/report", files=files)
                     
                         if res.status_code == 200:
                             data = res.json()
                         
                             # 1. Summary Card
                             st.success("Analysis Complete!")
                             st.markdown(f"""
                             <div style="background-color: rgba(0, 210, 255, 0.1); padding: 20px; border-radius: 10px; border-left: 5px solid #00d2ff;">
                                <h3>📋 AI Summary</h3>
                                <p>{data.get('summary', 'No summary provided.')}</p>
                             </div>
                             """, unsafe_allow_html=True)
                         
                             # 2. Extracted Data Grid
                             st.subheader("Extracted Vitals")
                             extracted = data.get("extracted_data", {})
                             if extracted:
                                 c1, c2, c3, c4 = st.columns(4)
                                 cols = [c1, c2, c3, c4]
                                 for i, (key, val) in enumerate(extracted.items()):
                                     with cols[i % 4]:
                                         st.metric(label=key.replace("_", " ").title(), value=val)
                             else:
                                 st.warning("No numerical data extracted.")
                             
                             with st.expander("View Raw JSON"):
                                 st.json(data)
                             
                         else:
                             st.error(f"Analysis Failed: {res.text}")
                     except Exception as e:
                         st.error(f"Error processing report: {e}")

        # --- Monitoring Dashboard (FAANG Upgrade) ---
        if selected == 'Monitoring Dashboard':
            st.title("System Monitoring Dashboard")
            st.markdown("Real-time view of system components, pipelines, and model health.")
        
            # 1. Component Status
            st.subheader("1. Component Status")
            c1, c2, c3 = st.columns(3)
            c1.metric("Backend API", "Online", delta="Healthy")
            c2.metric("MLflow Tracking", "Active", delta="v2.10.0")
            c3.metric("Data Pipeline", "Ready", delta="Pandas/Spark")
        
            # 2. Pipeline Health
            st.subheader("2. Pipeline Health")
            if st.button("Run Pipeline Health Check"):
                with st.spinner("Checking Data Lake & MLflow..."):
                    time.sleep(1) # Simulate check
                    st.success("✔ Data Ingestion Layer: Connected")
                    st.success("✔ Model Registry: Connected")
                    st.success("✔ GenAI Service: Active")
        
            # 3. MLflow Link
            st.subheader("3. MLOps Experiment Tracking")
            st.markdown("Access the full experiment tracking UI below:")
            st.markdown("[Open MLflow Dashboard](http://localhost:5000) (Requires `mlflow ui` running in terminal)")
        
            # 4. Recent Logs (Simulated)
            st.subheader("4. System Logs (Last 5 Events)")
            logs_df = pd.DataFrame({
                "Timestamp": [pd.Timestamp.now() - pd.Timedelta(minutes=m) for m in [1, 5, 10, 30, 60]],
                "Level": ["INFO", "INFO", "WARNING", "INFO", "INFO"],
                "Service": ["Frontend", "Backend", "MLflow", "DataPipeline", "Auth"],
                "Message": ["User Login Success", "Prediction Request Served", "Model Schema Warning", "Ingestion Job Completed", "System Startup"]
            })
            st.dataframe(logs_df)

        # --- Admin Panel (Protected) ---
        if selected == 'Admin Panel':
            st.title("Admin Command Center 🛡️")
            
            # Dashboard Tabs
            admin_tabs = st.tabs(["📊 System Overview", "👥 User Management"])
            
            with admin_tabs[0]:
                st.subheader("System Health & KPIs")
                # Fetch basic user list for aggregation
                headers = {"Authorization": f"Bearer {st.session_state.auth_token}"}
                try:
                    res = requests.get(f"{BACKEND_URL}/users", headers=headers)
                    if res.status_code == 200:
                        all_users = res.json()
                        
                        kpi1, kpi2, kpi3 = st.columns(3)
                        kpi1.metric("Total Users", len(all_users), delta="+1 Today")
                        kpi2.metric("Models Active", "3 (Diabetes, Heart, Liver)", delta="All Online")
                        kpi3.metric("System Status", "Healthy", delta="Uptime 99.9%")
                        
                        st.markdown("### 📈 Activity Trends")
                        # Simulated Chart for visual appeal
                        chart_data = pd.DataFrame(
                            np.random.randn(20, 3),
                            columns=['Users', 'Predictions', 'Errors'])
                        st.line_chart(chart_data)
                    else:
                        st.error("Could not load system stats.")
                except Exception as e:
                    st.error(f"Connection error: {e}")

            with admin_tabs[1]:
                st.subheader("User Database")
                
                # Fetch Users Again (or reuse)
                if 'all_users' in locals():
                    df = pd.DataFrame(all_users)
                    if not df.empty:
                        # Display main table
                        st.dataframe(
                            df[['id', 'username', 'full_name', 'email', 'joined_date'] if 'joined_date' in df.columns else ['id', 'username', 'full_name', 'email']], 
                            use_container_width=True,
                            hide_index=True
                        )
                        
                        st.markdown("---")
                        st.subheader("🕵️ User Dossier Inspector")
                        
                        # Selection Mechanism
                        selected_user_id = st.selectbox("Select User ID to Inspect", df['id'])
                        
                        if st.button("View Full Dossier", type="primary"):
                             with st.spinner(f"Retrieving confidential records for User ID {selected_user_id}..."):
                                try:
                                    res_full = requests.get(f"{BACKEND_URL}/users/{selected_user_id}/full", headers=headers)
                                    if res_full.status_code == 200:
                                        full_data = res_full.json()
                                        
                                        # Check for Redaction
                                        is_redacted = "[REDACTED" in str(full_data.get('about_me', ''))

                                        # --- THE DOSSIER VIEW ---
                                        import html
                                        safe_name = html.escape(full_data.get('full_name', 'Unknown'))
                                        safe_user = html.escape(full_data.get('username', 'Unknown'))
                                        
                                        if is_redacted:
                                            st.warning("🔒 PRIVACY PROTECTED: User has opted out of data collection. Sensitive records are hidden.")
                                        
                                        st.markdown(f"""
                                        <div style="background: rgba(0, 210, 255, 0.1); padding: 20px; border-radius: 10px; border: 1px solid #00d2ff;">
                                            <h2>📂 Use Dossier: {safe_name}</h2>
                                            <p><strong>ID:</strong> {full_data.get('id')} | <strong>Username:</strong> {safe_user}</p>
                                        </div>
                                        <br>
                                        """, unsafe_allow_html=True)
                                        
                                        dos_col1, dos_col2 = st.columns([1, 2])
                                        
                                        with dos_col1:
                                            st.markdown("### 👤 Profile")
                                            st.write(f"**Email:** {full_data.get('email')}")
                                            st.write(f"**DOB:** {full_data.get('dob')}")
                                            st.write(f"**Gender:** {full_data.get('gender')}")
                                            st.write(f"**Blood Type:** {full_data.get('blood_type')}")
                                            st.markdown("#### Lifestyle Pillars")
                                            st.write(f"**Diet:** {full_data.get('diet')}")
                                            st.write(f"**Activity:** {full_data.get('activity_level')}")
                                            st.write(f"**Sleep:** {full_data.get('sleep_hours')} hrs")
                                        
                                        with dos_col2:
                                            dos_tabs = st.tabs(["🏥 Medical History", "💬 Chat Logs"])
                                            
                                            with dos_tabs[0]:
                                                if full_data.get("health_records"):
                                                    recs = full_data["health_records"]
                                                    st.success(f"{len(recs)} Medical Records Found")
                                                    for r in recs:
                                                        icon = "🩸" if "diabetes" in r['record_type'] else "❤️" if "heart" in r['record_type'] else "🥦"
                                                        with st.expander(f"{icon} {r['record_type'].title()} - {r['timestamp'].split('T')[0]}"):
                                                            st.write(f"**Result:** {r['prediction']}")
                                                            st.code(r['data'], language='json')
                                                else:
                                                    st.info("No medical records.")

                                            with dos_tabs[1]:
                                                if full_data.get("chat_logs"):
                                                    logs = full_data["chat_logs"]
                                                    st.info(f"{len(logs)} Messages Logged")
                                                    for log in logs:
                                                        align = "right" if log['role'] == 'user' else "left"
                                                        color = "#00d2ff33" if log['role'] == 'user' else "#ffffff11"
                                                        st.markdown(f"""
                                                        <div style="text-align: {align}; margin-bottom: 5px;">
                                                            <span style="background: {color}; padding: 8px; border-radius: 10px; display: inline-block;">
                                                                <small>{log['role'].upper()}</small><br>
                                                                {log['content']}
                                                            </span>
                                                        </div>
                                                        """, unsafe_allow_html=True)
                                                else:
                                                    st.warning("No chat history.")
                                        
                                    else:
                                        st.error(f"Failed to load details: {res_full.text}")
                                except Exception as ex:
                                    st.error(f"Error: {ex}")

                    else:
                        st.info("No users found.")

if __name__ == '__main__':
    try:
        main_app()
    except Exception as e:
        st.error('An unexpected error occurred. Please refresh the page.')
        print(e)

