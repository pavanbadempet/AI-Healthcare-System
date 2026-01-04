
import google.generativeai as genai
import os
import json
import logging
from dotenv import load_dotenv
from PIL import Image
import io
from typing import Dict, Any, Union
from fastapi import HTTPException

# --- Logging ---
# logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Configuration ---
load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")


# Validated at runtime
# if not GOOGLE_API_KEY: ...

_vision_model = None

def get_vision_model():
    global _vision_model
    if _vision_model:
        return _vision_model
        
    if not GOOGLE_API_KEY:
        logger.warning("GOOGLE_API_KEY not found. Vision features will fail.")
        return None
        
    try:
        genai.configure(api_key=GOOGLE_API_KEY)
        _vision_model = genai.GenerativeModel('gemini-1.5-flash')
    except Exception as e:
        logger.error(f"Vision Model Init Failed: {e}")
        return None
    return _vision_model

# Removed global model = ...

def analyze_lab_report(image_bytes: bytes) -> Dict[str, Any]:
    """
    Analyzes a medical lab report image using Google Gemini Vision.
    
    Args:
        image_bytes (bytes): Raw image data (JPEG/PNG).
        
    Returns:
        dict: Structured JSON containing 'extracted_data' (metrics) and 'summary'.
    """
    try:
        if not GOOGLE_API_KEY:
            raise HTTPException(status_code=503, detail="Vision API Key not configured")


        image = Image.open(io.BytesIO(image_bytes))
        

        prompt = """
        You are an expert Medical AI. Analyze this lab report image.
        
        TASKS:
        1. Extract all visible numerical health metrics.
        2. specifically look for: 'glucose', 'hba1c', 'cholesterol', 'total_bilirubin', 'trestbps' (blood pressure), 'thalach' (heart rate).
        3. Provide a brief medical summary of the report.
        
        OUTPUT FORMAT (JSON):
        {
            "extracted_data": {
                "glucose": 0.0,
                "hba1c": 0.0,
                "cholesterol": 0.0,
                "total_bilirubin": 0.0,
                "trestbps": 0.0,
                "thalach": 0.0,
                ... (any other found metrics)
            },
            "summary": "The patient has elevated cholesterol..."
        }
        Return ONLY valid JSON. Do not include markdown formatting like ```json.
        """
        
        model = get_vision_model()
        if not model:
            raise HTTPException(status_code=503, detail="Vision Model Unavailable")
            
        response = model.generate_content([prompt, image])
        

        text = response.text.replace("```json", "").replace("```", "").strip()
        

        result = json.loads(text)
        return result

    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Vision Analysis Failed: {e}")
        return {
            "extracted_data": {},
            "summary": "Could not analyze the image. Please ensure the text is clear."
        }
