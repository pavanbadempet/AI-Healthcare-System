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
            
        # TABS for Management
        tab1, tab2 = st.tabs(["👥 User Management", "📅 Global Appointments"])
        
        # --- TAB 1: USERS ---
        with tab1:
            st.subheader("User Database")
            users_resp = requests.get(f"{backend_url}/admin/users", headers=headers, timeout=5)
            if users_resp.status_code == 200:
                users = users_resp.json()
                if users:
                    # Convert to DataFrame
                    import pandas as pd
                    df = pd.DataFrame(users)
                    if 'role' not in df.columns: df['role'] = 'patient'
                    
                    # Display Table
                    st.dataframe(
                        df[['id', 'username', 'role', 'full_name', 'email', 'joined']], 
                        use_container_width=True, 
                        hide_index=True
                    )
                    
                    st.divider()
                    
                    # Actions Section
                    c1, c2 = st.columns(2)
                    
                    # Edit Role
                    with c1:
                        with st.expander("✏️ Edit User Role"):
                            user_names = {f"{u['username']} (ID: {u['id']})": u for u in users}
                            sel_u = st.selectbox("Select User", list(user_names.keys()), key="role_sel")
                            target_user = user_names[sel_u]
                            new_r = st.selectbox("New Role", ["patient", "doctor", "admin"], key="role_val", index=["patient", "doctor", "admin"].index(target_user.get('role','patient')))
                            
                            if st.button("Update Role", type="primary"):
                                if api.update_user_role(target_user['id'], new_r):
                                    st.success(f"Updated {target_user['username']} to {new_r}!")
                                    st.rerun()

                    # Delete User
                    with c2:
                         with st.expander("🗑️ Delete User"):
                            st.warning("⚠️ This action is permanent!")
                            del_u = st.selectbox("Select User to Delete", list(user_names.keys()), key="del_sel")
                            target_del = user_names[del_u]
                            
                            if st.button(f"DELETE {target_del['username']}", type="secondary"):
                                if api.delete_user(target_del['id']):
                                    st.success(f"Deleted {target_del['username']}")
                                    st.rerun()
                else:
                    st.info("No users found.")
            else:
                st.error("Failed to fetch users.")

        # --- TAB 2: APPOINTMENTS ---
        with tab2:
            st.subheader("Appointment Operations")
            
            appointments = api.fetch_appointments()
            if appointments:
                # Filter
                status_filter = st.selectbox("Filter by Status", ["All", "Scheduled", "Completed", "Cancelled", "Rescheduled"])
                filtered_appts = [a for a in appointments if status_filter == "All" or a['status'] == status_filter]
                
                if filtered_appts:
                    for appt in filtered_appts:
                        date_str = appt['date_time'].replace("T", " ")[:16]
                        color = "#34D399" if appt['status'] in ['Scheduled', 'Rescheduled'] else "#94A3B8"
                        
                        with st.expander(f"{date_str} | {appt['specialist']} (ID: {appt['id']})"):
                            c_a, c_b = st.columns([3, 1])
                            with c_a:
                                st.markdown(f"**Patient ID:** `{appt['user_id']}`")
                                st.markdown(f"**Status:** <span style='color:{color}'>{appt['status']}</span>", unsafe_allow_html=True)
                                st.markdown(f"**Reason:** {appt['reason']}")
                            
                            with c_b:
                                if st.button("🗑️ Delete", key=f"del_apt_{appt['id']}"):
                                    if api.delete_appointment(appt['id']):
                                        st.success("Deleted!")
                                        st.rerun()
                else:
                    st.info(f"No {status_filter} appointments found.")
            else:
                st.info("No appointments in system.")
        
    except Exception as e:
        st.error(f"Connection Error: {e}")
