"""
Admin Dashboard View
====================
System analytics and user management.
"""
import streamlit as st
import requests
from frontend.utils import api

def render_admin_page():
    st.markdown("""
<div style="text-align: center; margin-bottom: 2rem;">
    <h1>🛡️ Clinic Admin Console</h1>
    <p style="color: #64748B;">Facility Overview & Patient Management</p>
</div>
""", unsafe_allow_html=True)
    
    # 1. Fetch Stats from Backend
    try:
        backend_url = api.get_backend_url()
        token = st.session_state.get('token', "")
        headers = {"Authorization": f"Bearer {token}"}
        
        response = requests.get(f"{backend_url}/admin/stats", headers=headers, timeout=5)
        
        if response.status_code == 403:
            st.error("⛔ Access Denied. You are not an administrator.")
            st.info("Log in as 'admin' to view this page.")
            return
            
        if response.status_code != 200:
            st.error(f"Failed to fetch stats: {response.text}")
            return
            
        stats = response.json()
        
        # 2. Display Metrics
        c1, c2, c3 = st.columns(3)
        c1.metric("Total Users", stats.get("total_users", 0))
        c2.metric("Total Predictions", stats.get("total_predictions", 0))
        c3.metric("Total Chats", stats.get("total_messages", 0))
        
        st.markdown("---")
        
        # 3. Server Status
        st.subheader("📡 System Status")
        col1, col2 = st.columns(2)
        with col1:
            st.success(f"API Server: {stats.get('server_status', 'Unknown')}")
        with col2:
            st.success(f"Database: {stats.get('database_status', 'Unknown')}")
            
        # 4. Recent Users
        st.subheader("👥 Recent Users")
        
        users_resp = requests.get(f"{backend_url}/admin/users", headers=headers, timeout=5)
        if users_resp.status_code == 200:
            users = users_resp.json()
            if users:
                st.table(users)
            else:
                st.caption("No users found.")
        
    except Exception as e:
        st.error(f"Connection Error: {e}")
