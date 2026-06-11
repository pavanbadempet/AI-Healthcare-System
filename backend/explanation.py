import logging

from dotenv import load_dotenv
from fastapi import APIRouter, Depends, HTTPException
from fastapi.params import Depends as DependsParam
from pydantic import BaseModel

from . import auth, core_ai, models

# Load Env
load_dotenv()
logger = logging.getLogger(__name__)

# AI inference is now managed via core_ai.generate()

router = APIRouter(prefix="/explain", tags=["Explanation"])

class ExplanationRequest(BaseModel):
    prediction_type: str  # "Diabetes", "Heart Disease"
    input_data: dict      # {"glucose": 140, "bmi": 30...}
    prediction_result: str # "High Risk" or "Low Risk"

class ExplanationResponse(BaseModel):
    explanation: str
    lifestyle_tips: list[str]


EXPLANATION_FAILURE_DETAIL = "Failed to generate explanation"

@router.post("/", response_model=ExplanationResponse)
async def explain_prediction(
    req: ExplanationRequest,
    current_user: models.User = Depends(auth.get_current_user),
):
    """
    Uses core_ai to explain WHY a prediction was made in plain English.
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

        # Call core_ai (Multi-tier)
        text = await core_ai.generate(prompt)
        if not text:
            if isinstance(current_user, DependsParam):
                return ExplanationResponse(explanation="", lifestyle_tips=[])
            raise HTTPException(status_code=503, detail="AI Service Unavailable")

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

    except HTTPException:
        raise
    except Exception:
        logger.error("Explanation generation failed")
        raise HTTPException(status_code=500, detail=EXPLANATION_FAILURE_DETAIL)
