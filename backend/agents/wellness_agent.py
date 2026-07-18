import json
import logging

from sqlalchemy.orm import Session

from backend.agents.base_agent import BaseAgent
from backend.core_ai import generate
from backend.prompt_registry import get_prompt

logger = logging.getLogger(__name__)

class ClinicalWellnessAgent(BaseAgent):
    """
    State-of-the-Art (SOTA) Personal Wellness & Lifestyle Preventive Advisory Agent.
    Generates personalized health recommendations and clinical disclaimers for patient care.
    """

    def __init__(self, db: Session, name: str = "AI Healthcare System Wellness Companion"):
        super().__init__(name)
        self.db = db

    async def generate_wellness_plan(self, patient_data: str) -> dict:
        """
        Analyzes lifestyle records and minor symptom descriptions to generate wellness guidance.
        """
        self.start()

        if not patient_data or not patient_data.strip():
            patient_data = "Symptom: Mild fatigue. Diet: High sodium. Activity: 1 hour sedentary work, no exercise."

        self.log_step("Analyze Lifestyle Data", "Calling SOTA Wellness Advisory LLM...")
        prompt = get_prompt("wellness_advisory_analysis").format(
            patient_data=patient_data
        )
        self.estimate_tokens(prompt)
        raw_output = await generate(
            prompt=prompt,
            system="You are a SOTA patient wellness, lifestyle, and preventive care advisor. Output valid JSON only."
        )
        self.estimate_tokens(raw_output, is_output=True)

        try:
            clean_str = raw_output.strip()
            if clean_str.startswith("```json"):
                clean_str = clean_str[7:]
            if clean_str.endswith("```"):
                clean_str = clean_str[:-3]
            clean_str = clean_str.strip()

            structured_report = json.loads(clean_str)
            self.log_step("Parse Wellness Report", "Successfully parsed structured wellness and advisory report.")
            self.finish("completed")
            return {
                "telemetry": {
                    "duration": self.duration,
                    "input_tokens": self.input_tokens_estimated,
                    "output_tokens": self.output_tokens_estimated,
                },
                "status": "completed",
                "report": structured_report
            }
        except Exception as e:
            self.log_error(f"Failed to parse wellness plan: {e}")
            self.finish("failed")
            return {
                "error": "Failed to parse structured wellness and advisory report.",
                "raw_output": raw_output
            }
