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
    cm.set("auth_token", token, expires_at=expires, key="set_token")
    cm.set("auth_username", username, expires_at=expires, key="set_user")

def load_session() -> Optional[Dict[str, str]]:
    cm = _get_cookie_manager()
    token, username = cm.get("auth_token"), cm.get("auth_username")
    return {"token": token, "username": username} if token and username else None

def clear_session():
    cm = _get_cookie_manager()
    cm.delete("auth_token", key="del_token")
    cm.delete("auth_username", key="del_user")
    st.session_state.pop('token', None)
    st.session_state.pop('username', None)


# --- Auth ---

def login(username, password) -> bool:
    try:
        resp = requests.post(f"{BACKEND_URL}/token", data={"username": username, "password": password})
        if resp.status_code == 200:
            token = resp.json()['access_token']
            st.session_state['token'] = token
            st.session_state['username'] = username
            save_session(token, username)
            return True
        st.error(f"Login Failed: {resp.json().get('detail', 'Error')}")
    except Exception as e:
        st.error(f"Connection Error: {e}")
    return False

def signup(username, password, email, full_name, dob) -> bool:
    try:
        resp = requests.post(f"{BACKEND_URL}/signup", json={
            "username": username, "password": password, "email": email, "full_name": full_name, "dob": str(dob)
        })
        if resp.status_code == 200:
            return True
        st.error(f"Signup Failed: {resp.json().get('detail', 'Error')}")
    except Exception as e:
        st.error(f"Connection Error: {e}")
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


# --- Records ---

def fetch_records(record_type: Optional[str] = None) -> List[Dict]:
    if 'token' not in st.session_state: return []
    url = f"{BACKEND_URL}/records" + (f"?record_type={record_type}" if record_type else "")
    try:
        resp = requests.get(url, headers=_headers())
        return resp.json() if resp.status_code == 200 else []
    except Exception:
        return []

def save_record(record_type, data, prediction):
    if 'token' not in st.session_state: return
    try:
        requests.post(f"{BACKEND_URL}/records", json={"record_type": record_type, "data": data, "prediction": prediction}, headers=_headers())
    except Exception:
        pass

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
