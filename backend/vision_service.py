
import io
import json
import logging
from typing import Any, Dict

from fastapi import HTTPException
from PIL import Image

from . import core_ai
from .prompt_registry import get_prompt

# --- Logging ---
# logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def analyze_lab_report(image_bytes: bytes) -> Dict[str, Any]:
    """
    Analyzes a medical lab report image using Google Gemini Vision.

    Args:
        image_bytes (bytes): Raw image data (JPEG/PNG).

    Returns:
        dict: Structured JSON containing 'extracted_data' (metrics) and 'summary'.
    """
    try:
        if not core_ai.has_gemini_api_key():
            raise HTTPException(status_code=503, detail="Vision API Key not configured")


        image = Image.open(io.BytesIO(image_bytes))

        prompt = get_prompt("lab_report_vision")

        text = core_ai.generate_vision_content(prompt, image)
        if not text:
            raise HTTPException(status_code=503, detail="Vision Model Unavailable")

        text = text.replace("```json", "").replace("```", "").strip()


        result = json.loads(text)
        return result

    except HTTPException as he:
        raise he
    except Exception:
        logger.error("Vision analysis failed")
        return {
            "extracted_data": {},
            "summary": "Could not analyze the image. Please ensure the text is clear."
        }


def analyze_lab_report_pdf(pdf_bytes: bytes) -> Dict[str, Any]:
    """
    Analyzes a medical lab report PDF using Google Gemini (1.5 Flash).
    """
    try:
        if not core_ai.has_gemini_api_key():
            raise HTTPException(status_code=503, detail="Vision API Key not configured")

        import google.generativeai as genai
        genai.configure(api_key=core_ai.GOOGLE_API_KEY)
        model = genai.GenerativeModel(core_ai.GEMINI_VISION_MODEL)

        prompt = get_prompt("lab_report_vision")

        response = model.generate_content([
            {
                'mime_type': 'application/pdf',
                'data': pdf_bytes
            },
            prompt
        ])

        text = (getattr(response, "text", "") or "").strip()
        text = text.replace("```json", "").replace("```", "").strip()
        result = json.loads(text)
        return result
    except Exception as e:
        logger.error("PDF analysis failed: %s", e)
        return {
            "extracted_data": {},
            "summary": "Could not analyze the PDF report. Please ensure the file is not password-protected and contains clear text."
        }
