"""Frontend API Client"""
import requests
import streamlit as st
import os
from typing import Optional, Dict, Any, List
import extra_streamlit_components as stx
from datetime import datetime, timedelta

# Backend URL
try:
    BACKEND_URL = os.getenv("BACKEND_URL") or st.secrets.get("BACKEND_URL") or "http://127.0.0.1:8000"
except FileNotFoundError:
    BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8000")

def get_backend_url(): return BACKEND_URL

import uuid

# --- Session Management ---

def _get_cookie_manager():
    # Ensure cookie manager is initialized in main.py
    if 'cookie_manager' not in st.session_state:
        # Fallback (should typically be handled in main)
        st.session_state['cookie_manager'] = stx.CookieManager(key="init")
    return st.session_state['cookie_manager']

def save_session(token: str, username: str):
    cm = _get_cookie_manager()
    expires = datetime.now() + timedelta(days=7)
    # Use unique keys to force the component to update
    cm.set("auth_token", token, expires_at=expires, key=f"set_token_{uuid.uuid4()}")
    cm.set("auth_username", username, expires_at=expires, key=f"set_user_{uuid.uuid4()}")

def load_session() -> Optional[Dict[str, str]]:
    cm = _get_cookie_manager()
    # No unique need for get, as it just reads current state
    token, username = cm.get("auth_token"), cm.get("auth_username")
    return {"token": token, "username": username} if token and username else None

def clear_session():
    cm = _get_cookie_manager()
    # Check if cookie exists before deleting to avoid KeyError
    try:
        if cm.get("auth_token"):
            cm.delete("auth_token", key=f"del_token_{uuid.uuid4()}")
    except Exception:
        pass
    try:
        if cm.get("auth_username"):
            cm.delete("auth_username", key=f"del_user_{uuid.uuid4()}")
    except Exception:
        pass
    st.session_state.pop('token', None)
    st.session_state.pop('username', None)


# --- Auth ---

def _format_error(detail):
    """Format API error detail into user-friendly message."""
    if isinstance(detail, list):
        # Validation errors come as list of dicts
        messages = []
        for err in detail:
            field = err.get('loc', ['', 'field'])[-1]
            msg = err.get('msg', 'Invalid')
            messages.append(f"{field.replace('_', ' ').title()}: {msg}")
        return "; ".join(messages) if messages else "Validation error"
    return str(detail) if detail else "An error occurred"

def login(username, password) -> bool:
    if not username or not password:
        st.error("Please enter both username and password")
        return False
    try:
        resp = requests.post(f"{BACKEND_URL}/token", data={"username": username, "password": password})
        if resp.status_code == 200:
            token = resp.json()['access_token']
            st.session_state['token'] = token
            st.session_state['username'] = username
            save_session(token, username)
            
            # Fetch profile to get Role and Picture
            try:
                prof = fetch_profile()
                if prof:
                    st.session_state['role'] = prof.get('role', 'patient')
                    st.session_state['profile_picture'] = prof.get('profile_picture')
            except:
                pass
                
            return True
        detail = resp.json().get('detail', 'Invalid credentials')
        st.error(f"Login Failed: {_format_error(detail)}")
    except Exception as e:
        st.error(f"Connection Error: Unable to reach server")
    return False

def signup(username, password, email, full_name, dob) -> bool:
    if not username or not password or not email:
        st.error("Please fill in all required fields")
        return False
    if len(password) < 8:
        st.error("Password must be at least 8 characters")
        return False
    try:
        resp = requests.post(f"{BACKEND_URL}/signup", json={
            "username": username, "password": password, "email": email, "full_name": full_name, "dob": str(dob)
        })
        if resp.status_code == 200:
            return True
        detail = resp.json().get('detail', 'Signup failed')
        st.error(f"Signup Failed: {_format_error(detail)}")
    except Exception as e:
        st.error(f"Connection Error: Unable to reach server")
    return False


# --- Profile ---

def _headers():
    return {"Authorization": f"Bearer {st.session_state.get('token', '')}"}

def fetch_profile() -> Optional[Dict[str, Any]]:
    if 'token' not in st.session_state: return None
    try:
        resp = requests.get(f"{BACKEND_URL}/profile", headers=_headers())
        return resp.json() if resp.status_code == 200 else None
    except Exception:
        return None

def update_profile(data: Dict[str, Any]) -> bool:
    try:
        resp = requests.put(f"{BACKEND_URL}/profile", json=data, headers=_headers())
        if resp.status_code == 200:
            st.success("Profile Updated!")
            return True
        st.error("Update failed")
    except Exception as e:
        st.error(f"Error: {e}")
    return False

def fetch_health_report() -> Optional[bytes]:
    """Fetch the PDF health report with auth headers."""
    if 'token' not in st.session_state: return None
    try:
        resp = requests.get(f"{BACKEND_URL}/download/health-report", headers=_headers())
        if resp.status_code == 200:
            return resp.content
    except Exception as e:
        print(f"Error fetching report: {e}")
    return None

# --- Records ---

def fetch_records(record_type: Optional[str] = None) -> List[Dict]:
    if 'token' not in st.session_state: return []
    url = f"{BACKEND_URL}/records" + (f"?record_type={record_type}" if record_type else "")
    try:
        resp = requests.get(url, headers=_headers())
        return resp.json() if resp.status_code == 200 else []
    except Exception as e:
        print(f"Error fetching records: {e}")
        return []

def save_record(record_type, data, prediction):
    if 'token' not in st.session_state: return
    try:
        requests.post(f"{BACKEND_URL}/records", json={"record_type": record_type, "data": data, "prediction": prediction}, headers=_headers())
    except Exception as e:
        st.toast(f"Failed to save record: {e}", icon="❌")

def delete_record(record_id: int):
    try:
        resp = requests.delete(f"{BACKEND_URL}/records/{record_id}", headers=_headers())
        if resp.status_code == 200:
            st.rerun()
    except Exception as e:
        st.error(f"Delete failed: {e}")


# --- Predictions ---

def get_prediction(endpoint: str, data: Dict) -> Dict:
    try:
        resp = requests.post(f"{BACKEND_URL}/predict/{endpoint}", json=data)
        return resp.json() if resp.status_code == 200 else {"error": resp.json().get('detail', 'Failed')}
    except Exception as e:
        return {"error": str(e)}

def get_explanation(endpoint: str, data: Dict) -> str:
    try:
        resp = requests.post(f"{BACKEND_URL}/predict/explain/{endpoint}", json=data)
        return resp.json().get("html_plot", "") if resp.status_code == 200 else ""
    except Exception:
        return ""

def get_ai_explanation(prediction_type: str, inputs: Dict, result: str) -> Dict:
    if 'token' not in st.session_state: return {}
    try:
        resp = requests.post(f"{BACKEND_URL}/explain/", json={
            "prediction_type": prediction_type, "input_data": inputs, "prediction_result": result
        }, headers=_headers())
        return resp.json() if resp.status_code == 200 else {}
    except Exception:
        return {}


# --- Payments ---

def create_payment_order(amount_paise: int, plan_id: str):
    try:
        resp = requests.post(f"{BACKEND_URL}/payments/create-order", json={
            "amount": amount_paise, "currency": "INR", "plan_id": plan_id
        }, headers=_headers())
        return resp.json() if resp.status_code == 200 else None
    except Exception:
        return None


# --- Telemedicine ---

def fetch_doctors() -> List[Dict]:
    if 'token' not in st.session_state: return []
    try:
        resp = requests.get(f"{BACKEND_URL}/appointments/doctors", headers=_headers())
        return resp.json() if resp.status_code == 200 else []
    except Exception:
        return []

def book_appointment(data: Dict) -> bool:
    if 'token' not in st.session_state: return False
    try:
        resp = requests.post(f"{BACKEND_URL}/appointments/", json=data, headers=_headers())
        if resp.status_code == 200:
            return True
        st.error(f"Booking Failed: {_format_error(resp.json().get('detail'))}")
    except Exception as e:
        st.error(f"Error: {e}")
    return False

def fetch_appointments() -> List[Dict]:
    if 'token' not in st.session_state: return []
    try:
        resp = requests.get(f"{BACKEND_URL}/appointments/", headers=_headers())
        return resp.json() if resp.status_code == 200 else []
    except Exception:
        return []
