
import google.generativeai as genai
import os
import json
from dotenv import load_dotenv
from PIL import Image
import io

load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

if not GOOGLE_API_KEY:
    raise ValueError("GOOGLE_API_KEY not found in .env file")

genai.configure(api_key=GOOGLE_API_KEY)

# Use Gemini 2.0 Flash for speed and vision capabilities
model = genai.GenerativeModel('gemini-2.0-flash')

def analyze_lab_report(image_bytes: bytes):
    """
    Analyzes a medical lab report image and returns structured JSON data + summary.
    """
    try:
        # Load Image
        image = Image.open(io.BytesIO(image_bytes))
        
        # Prompt for extraction
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
        
        response = model.generate_content([prompt, image])
        
        # Clean response
        text = response.text.replace("```json", "").replace("```", "").strip()
        
        # Parse JSON
        result = json.loads(text)
        return result

    except Exception as e:
        print(f"Vision Error: {e}")
        return {
            "extracted_data": {},
            "summary": "Could not analyze the image. Please ensure the text is clear."
        }
