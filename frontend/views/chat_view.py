"""
Health Assistant Chat View
================================================
Modern chat interface with typing indicators, reactions, and enhanced UX.
"""
import streamlit as st
import requests
from frontend.utils import api

BACKEND_URL = api.BACKEND_URL


def render_chat_page():
    """Render the premium AI Health Assistant chat interface."""
    
    # Inject custom CSS for chat styling
    st.markdown("""
    <style>
    /* Chat container styling */
    .stChatMessage {
        background: transparent !important;
        padding: 0.5rem 0 !important;
    }
    
    /* User message bubble */
    .stChatMessage[data-testid="stChatMessageContent-user"] {
        background: linear-gradient(135deg, rgba(59, 130, 246, 0.2), rgba(59, 130, 246, 0.1)) !important;
        border: 1px solid rgba(59, 130, 246, 0.2) !important;
        border-radius: 18px 18px 4px 18px !important;
        padding: 1rem 1.25rem !important;
    }
    
    /* Assistant message bubble */
    .stChatMessage[data-testid="stChatMessageContent-assistant"] {
        background: rgba(30, 41, 59, 0.6) !important;
        border: 1px solid rgba(148, 163, 184, 0.1) !important;
        border-radius: 18px 18px 18px 4px !important;
        padding: 1rem 1.25rem !important;
    }
    
    /* Chat input styling */
    .stChatInput > div {
        background: rgba(15, 23, 42, 0.8) !important;
        border: 1px solid rgba(59, 130, 246, 0.2) !important;
        border-radius: 24px !important;
        padding: 0.5rem !important;
    }
    
    .stChatInput input {
        color: #F1F5F9 !important;
        font-size: 0.95rem !important;
    }
    
    .stChatInput button {
        background: linear-gradient(135deg, #3B82F6, #2563EB) !important;
        border-radius: 50% !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Header with icon and subtitle
    st.markdown("""
    <div style="margin-bottom: 2rem;">
        <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 0.5rem;">
            <span style="font-size: 2rem;">🤖</span>
            <h1 style="margin: 0; font-size: 1.75rem;">AI Health Assistant</h1>
        </div>
        <p style="color: #64748B; font-size: 0.9rem; margin: 0;">
            Ask me about symptoms, medications, lifestyle advice, and more. 
            <span style="color: #F59E0B;">⚠️ Not a substitute for professional medical advice.</span>
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Initialize session state
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    # Quick action buttons
    if len(st.session_state.messages) == 0:
        st.markdown("""
        <div style="
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            margin-bottom: 1.5rem;
        ">
            <div style="
                background: rgba(30, 41, 59, 0.5);
                border: 1px solid rgba(148, 163, 184, 0.1);
                border-radius: 20px;
                padding: 8px 16px;
                font-size: 0.85rem;
                color: #94A3B8;
            ">💊 "What are common diabetes symptoms?"</div>
            <div style="
                background: rgba(30, 41, 59, 0.5);
                border: 1px solid rgba(148, 163, 184, 0.1);
                border-radius: 20px;
                padding: 8px 16px;
                font-size: 0.85rem;
                color: #94A3B8;
            ">❤️ "How can I lower my cholesterol?"</div>
            <div style="
                background: rgba(30, 41, 59, 0.5);
                border: 1px solid rgba(148, 163, 184, 0.1);
                border-radius: 20px;
                padding: 8px 16px;
                font-size: 0.85rem;
                color: #94A3B8;
            ">🏃 "Best exercises for heart health?"</div>
        </div>
        """, unsafe_allow_html=True)
    
    # Display chat history
    for msg in st.session_state.messages:
        avatar = "🧑‍💻" if msg["role"] == "user" else "🤖"
        with st.chat_message(msg["role"], avatar=avatar):
            st.markdown(msg["content"])
    
    # Chat input
    if prompt := st.chat_input("Ask me about your health..."):
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user", avatar="🧑‍💻"):
            st.markdown(prompt)
        
        # Generate AI response
        with st.chat_message("assistant", avatar="🤖"):
            response_placeholder = st.empty()
            
            with st.spinner(""):
                # Show typing indicator
                response_placeholder.markdown("""
                <div style="display: flex; align-items: center; gap: 8px; color: #64748B;">
                    <div class="typing-indicator">
                        <span></span><span></span><span></span>
                    </div>
                    <span style="font-size: 0.85rem;">Thinking...</span>
                </div>
                <style>
                .typing-indicator {
                    display: flex;
                    gap: 4px;
                }
                .typing-indicator span {
                    width: 6px;
                    height: 6px;
                    background: #3B82F6;
                    border-radius: 50%;
                    animation: typing 1.4s infinite ease-in-out;
                }
                .typing-indicator span:nth-child(1) { animation-delay: 0s; }
                .typing-indicator span:nth-child(2) { animation-delay: 0.2s; }
                .typing-indicator span:nth-child(3) { animation-delay: 0.4s; }
                @keyframes typing {
                    0%, 80%, 100% { transform: scale(0.8); opacity: 0.5; }
                    40% { transform: scale(1.2); opacity: 1; }
                }
                </style>
                """, unsafe_allow_html=True)
                
                try:
                    # Check if token exists
                    token = st.session_state.get('token', '')
                    if not token:
                        ans = "⚠️ Please log in to use the AI Assistant."
                    else:
                        headers = {"Authorization": f"Bearer {token}"}
                        payload = {
                            "message": prompt,
                            "history": [
                                {"role": m["role"], "content": m["content"]} 
                                for m in st.session_state.messages[:-1]
                            ],
                            "current_context": {}
                        }
                        
                        resp = requests.post(
                            f"{BACKEND_URL}/chat", 
                            json=payload, 
                            headers=headers,
                            timeout=60
                        )
                        
                        if resp.status_code == 200:
                            data = resp.json()
                            ans = data.get("response", "I couldn't generate a response. Please try again.")
                            
                            # Check if AI is unavailable
                            if "AI Unavailable" in ans or "Unavailable" in ans:
                                ans = """🔧 **AI Service Temporarily Unavailable**

The AI assistant is currently offline. This usually means:
- The API key hasn't been configured on the server
- The AI service is experiencing issues

**In the meantime, you can:**
- Use the **Disease Prediction** tools in the sidebar
- Check your **Profile** for health stats
- Try again in a few minutes

*If this persists, please contact support.*"""
                        
                        elif resp.status_code == 401:
                            ans = "🔐 Your session has expired. Please log out and log in again."
                        
                        elif resp.status_code == 503:
                            ans = "🔧 The AI service is currently unavailable. Please try again later."
                        
                        else:
                            error_detail = resp.json().get('detail', 'Unknown error')
                            ans = f"⚠️ Something went wrong: {error_detail}\n\nPlease try again or use the prediction tools in the sidebar."
                
                except requests.exceptions.Timeout:
                    ans = "⏱️ The request timed out. The AI is taking longer than expected. Please try a simpler question."
                
                except requests.exceptions.ConnectionError:
                    ans = """🌐 **Connection Error**
                    
Unable to reach the AI server. Please check:
- Your internet connection
- The backend server status

Try refreshing the page or come back later."""
                
                except Exception as e:
                    ans = f"❌ An error occurred: {str(e)}\n\nPlease try again or use the prediction tools."
                
                # Display final response
                response_placeholder.markdown(ans)
                st.session_state.messages.append({"role": "assistant", "content": ans})
    
    # Clear chat button (subtle, at bottom)
    if len(st.session_state.messages) > 0:
        st.markdown("<br>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            if st.button("🗑️ Clear Chat", type="secondary", use_container_width=True):
                st.session_state.messages = []
                st.rerun()
