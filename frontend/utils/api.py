import requests
import streamlit as st
import json
import os
from typing import Optional, Dict, Any, List

# --- Configuration ---
# Allow override via env var (Render) or secrets (Streamlit Cloud), default to local
try:
    BACKEND_URL = os.getenv("BACKEND_URL") or st.secrets.get("BACKEND_URL") or "http://127.0.0.1:8000"
except FileNotFoundError:
    BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8000")

# --- Session Management ---
SESSION_FILE = "session.json"

def save_session(token: str, username: str):
    """
    Save session to st.session_state. 
    NOTE: File-based persistence is DISABLED for Streamlit Cloud security 
    (containers are shared).
    """
    pass # Managed purely in memory for now

def load_session() -> Optional[Dict[str, str]]:
    """Session loading disabled for stateless security on cloud."""
    return None

def clear_session():
    """Logout and clear session file."""
    if os.path.exists(SESSION_FILE):
        os.remove(SESSION_FILE)
    if 'token' in st.session_state:
        del st.session_state['token']
    if 'username' in st.session_state:
        del st.session_state['username']

# --- Auth API ---

def login(username, password) -> bool:
    try:
        data = {"username": username, "password": password}
        # FastAPI OAuth2PasswordRequestForm expects form data, not json
        resp = requests.post(f"{BACKEND_URL}/token", data=data) 
        if resp.status_code == 200:
            token_data = resp.json()
            st.session_state['token'] = token_data['access_token']
            st.session_state['username'] = username
            save_session(token_data['access_token'], username)
            return True
        else:
            st.error(f"Login Failed: {resp.json().get('detail', 'Unknown Error')}")
            return False
    except Exception as e:
        st.error(f"Connection Error: {e}")
        return False

def signup(username, password, email, full_name, dob) -> bool:
    try:
        print(f"DEBUG: Attempting signup for user: {username}")
        payload = {
            "username": username, 
            "password": password,
            "email": email,
            "full_name": full_name,
            "dob": str(dob)
        }
        resp = requests.post(f"{BACKEND_URL}/signup", json=payload)
        if resp.status_code == 200:
            return True
        else:
            st.error(f"Signup Failed: {resp.json().get('detail', 'Unknown Error')}")
            return False
    except Exception as e:
        st.error(f"Connection Error: {e}")
        return False

# --- User Data API ---

def fetch_profile() -> Optional[Dict[str, Any]]:
    if 'token' not in st.session_state: return None
    headers = {"Authorization": f"Bearer {st.session_state['token']}"}
    try:
        resp = requests.get(f"{BACKEND_URL}/profile", headers=headers)
        if resp.status_code == 200:
            return resp.json()
    except Exception:
        pass
    return None

def update_profile(data: Dict[str, Any]) -> bool:
    headers = {"Authorization": f"Bearer {st.session_state['token']}"}
    try:
        resp = requests.put(f"{BACKEND_URL}/profile", json=data, headers=headers)
        if resp.status_code == 200:
            st.success("Profile Updated!")
            return True
        else:
            st.error("Failed to update profile.")
            return False
    except Exception as e:
        st.error(f"Error: {e}")
        return False

# --- Records & Prediction API ---

def fetch_records(record_type: Optional[str] = None) -> List[Dict[str, Any]]:
    if 'token' not in st.session_state: return []
    headers = {"Authorization": f"Bearer {st.session_state['token']}"}
    try:
        url = f"{BACKEND_URL}/records"
        if record_type:
             url += f"?record_type={record_type}"
        resp = requests.get(url, headers=headers)
        if resp.status_code == 200:
            return resp.json()
    except Exception as e:
        st.error(f"Failed to fetch records: {e}")
    return []

def delete_record(record_id: int):
    headers = {"Authorization": f"Bearer {st.session_state['token']}"}
    try:
        requests.delete(f"{BACKEND_URL}/records/{record_id}", headers=headers)
        st.rerun()
    except Exception as e:
        st.error(f"Delete failed: {e}")

def save_record(record_type, data, prediction):
    if 'token' not in st.session_state: return
    headers = {"Authorization": f"Bearer {st.session_state['token']}"}
    payload = {
        "record_type": record_type,
        "data": data,
        "prediction": prediction
    }
    try:
        requests.post(f"{BACKEND_URL}/records", json=payload, headers=headers)
    except Exception as e:
        st.error(f"Failed to save record: {e}")

def get_prediction(endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """Generic prediction wrapper."""
    if 'token' not in st.session_state:
        # Fallback for unauthenticated access (if allowed) or error
        # Currently backend requires auth for everything? No, predict endpoints are open in main.py?
        # Let's check. Actually prediction endpoints in router don't have Depends(get_current_user).
        # So they are public.
        pass
        
    try:
        resp = requests.post(f"{BACKEND_URL}/predict/{endpoint}", json=data)
        if resp.status_code == 200:
            return resp.json()
        else:
             return {"error": resp.json().get('detail', 'Prediction Failed')}
    except Exception as e:
        return {"error": str(e)}

def get_explanation(endpoint: str, data: Dict[str, Any]) -> str:
    """Fetch SHAP explanation plot as HTML."""
    try:
        resp = requests.post(f"{BACKEND_URL}/predict/explain/{endpoint}", json=data)
        if resp.status_code == 200:
            return resp.json().get("html_plot", "")
    except Exception:
        pass
    return ""
