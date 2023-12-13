import streamlit as st
import requests
import os
from frontend.utils import api

BACKEND_URL = api.BACKEND_URL

def render_chat_page():
    st.header("💬 AI Health Assistant")
    
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display Chat History
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Chat Input
    if prompt := st.chat_input("Ask me about your health..."):
        # User Message
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # AI Response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    headers = {"Authorization": f"Bearer {st.session_state.get('token', '')}"}
                    # Send history for context
                    payload = {
                        "message": prompt,
                        "history": [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages[:-1]],
                        "current_context": {} # Populate if needed
                    }
                    resp = requests.post(f"{BACKEND_URL}/chat", json=payload, headers=headers)
                    if resp.status_code == 200:
                        ans = resp.json().get("response", "No response.")
                    else:
                        ans = "Sorry, I encountered an error."
                except Exception as e:
                    ans = f"Error: {e}"
                
                st.markdown(ans)
                st.session_state.messages.append({"role": "assistant", "content": ans})
