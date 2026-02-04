"""
Internationalization (i18n) Utilities
=====================================
Simple dictionary-based translation for the frontend.
"""
import streamlit as st

# --- Translation Dictionary ---
TRANSLATIONS = {
    "en": {
        "dashboard": "Dashboard",
        "chat": "AI Chat Assistant",
        "profile": "My Profile",
        "pricing": "Plans & Pricing",
        "telemedicine": "Telemedicine",
        "about": "About & Legal",
        "admin": "Admin Panel",
        "welcome": "Welcome back",
        "analyze": "Analyze Risk",
        "download_pdf": "Download Report",
        "diabetes_pred": "Diabetes",
        "heart_pred": "Heart Disease",
        "liver_pred": "Liver Disease",
        "kidney_pred": "Kidney Disease",
        "lung_pred": "Lung Cancer"
    },
    "hi": {
        "dashboard": "डैशबोर्ड",
        "chat": "एआई चैट सहायक",
        "profile": "मेरी प्रोफाइल",
        "pricing": "योजनाएं और मूल्य",
        "telemedicine": "टेलीमेडिसिन",
        "about": "हमारे बारे में",
        "admin": "एडमिन पैनल",
        "welcome": "वापसी पर स्वागत है",
        "analyze": "जोखिम विश्लेषण करें",
        "download_pdf": "रिपोर्ट डाउनलोड करें",
        "diabetes_pred": "मधुमेह भविष्यवाणी",
        "heart_pred": "हृदय रोग भविष्यवाणी",
        "liver_pred": "लिवर रोग भविष्यवाणी",
        "kidney_pred": "गुर्दा रोग भविष्यवाणी",
        "lung_pred": "फेफड़ों का कैंसर भविष्यवाणी"
    },
    "te": {
        "dashboard": "డ్యాష్‌బోర్డ్",
        "chat": "AI చాట్ అసిస్టెంట్",
        "profile": "నా ప్రొఫైల్",
        "pricing": "ప్రణాళికలు & ధరలు",
        "telemedicine": "టెలిమెడిసిన్",
        "about": "మా గురించి & చట్టపరమైన",
        "admin": "అడ్మిన్ ప్యానెల్",
        "welcome": "తిరిగి స్వాగతం",
        "analyze": "ప్రమాదాన్ని విశ్లేషించండి",
        "download_pdf": "నివేదికను డౌన్‌లోడ్ చేయండి",
        "diabetes_pred": "మధుమేహ అంచనా",
        "heart_pred": "గుండె జబ్బు అంచనా",
        "liver_pred": "కాలేయ వ్యాధి అంచనా",
        "kidney_pred": "మూత్రపిండ వ్యాధి అంచనా",
        "lung_pred": "ఊపిరితిత్తుల క్యాన్సర్ అంచనా"
    }
}

def get_text(key: str) -> str:
    """Get translated text for the current language."""
    lang = st.session_state.get('language', 'en')
    return TRANSLATIONS.get(lang, TRANSLATIONS['en']).get(key, key)

def render_language_selector():
    """Render a sidebar widget to switch languages."""
    lang = st.session_state.get('language', 'en')
    
    # Map codes to specific display names and indices
    options = ["English", "हिंदी (Hindi)", "తెలుగు (Telugu)"]
    codes = ["en", "hi", "te"]
    
    current_index = 0
    if lang == 'hi': current_index = 1
    if lang == 'te': current_index = 2
    
    selected_name = st.sidebar.selectbox(
        "🌐 Language",
        options,
        index=current_index,
        key="lang_selector"
    )
    
    # Update session state with code
    if selected_name == "English": st.session_state['language'] = 'en'
    elif selected_name == "हिंदी (Hindi)": st.session_state['language'] = 'hi'
    elif selected_name == "తెలుగు (Telugu)": st.session_state['language'] = 'te'

def get_english_key(text: str) -> str:
    """Find the English key for a given translated text."""
    # Search all languages
    for lang, mapping in TRANSLATIONS.items():
        for key, val in mapping.items():
            if val == text:
                return key
    return text.lower().replace(" ", "_") # Fallback, though likely won't work for menus
