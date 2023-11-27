from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
import google.generativeai as genai
import os
import logging
from dotenv import load_dotenv

# Load Env
load_dotenv()
logger = logging.getLogger(__name__)

# Config
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    logger.error("GOOGLE_API_KEY not found for Explanation Service")

genai.configure(api_key=GOOGLE_API_KEY)
# Align with agent.py model verson
model = genai.GenerativeModel("gemini-2.0-flash") 

router = APIRouter(prefix="/explain", tags=["Explanation"])

class ExplanationRequest(BaseModel):
    prediction_type: str  # "Diabetes", "Heart Disease"
    input_data: dict      # {"glucose": 140, "bmi": 30...}
    prediction_result: str # "High Risk" or "Low Risk"

class ExplanationResponse(BaseModel):
    explanation: str
    lifestyle_tips: list[str]

@router.post("/", response_model=ExplanationResponse)
async def explain_prediction(req: ExplanationRequest):
    """
    Uses Gemini to explain WHY a prediction was made in plain English.
    """
    try:
        # Construct Prompt
        prompt = f"""
        You are an expert Medical AI. I have just run a Machine Learning prediction for **{req.prediction_type}**.
        
        **Patient Data**:
        {req.input_data}
        
        **Model Prediction**:
        {req.prediction_result}
        
        **Task**:
        1. Explain WHY the model likely gave this result based on the provided data (e.g. "Your glucose of 140 is higher than normal...").
        2. Provide 3 specific, actionable lifestyle tips to improve this condition.
        3. Be empathetic but scientific.
        4. Return the response in a structured format with clear sections.
        
        Output Format:
        EXPLANATION: [Your explanation here]
        TIPS:
        - [Tip 1]
        - [Tip 2]
        - [Tip 3]
        """
        
        # Call Gemini
        response = model.generate_content(prompt)
        text = response.text
        
        # Naive parsing (could be improved with structured output mode if available)
        explanation_part = ""
        tips_part = []
        
        if "EXPLANATION:" in text:
            parts = text.split("TIPS:")
            explanation_part = parts[0].replace("EXPLANATION:", "").strip()
            if len(parts) > 1:
                tips_lines = parts[1].strip().split("\n")
                tips_part = [t.strip("- ").strip() for t in tips_lines if t.strip()]
        else:
            explanation_part = text # Fallback
            tips_part = ["Consult a doctor for personalized advice."]

        return ExplanationResponse(
            explanation=explanation_part,
            lifestyle_tips=tips_part
        )

    except Exception as e:
        logger.error(f"Explanation Error: {e}")
        # Return actual error for debugging
        raise HTTPException(status_code=500, detail=f"Failed to generate explanation: {str(e)}")
