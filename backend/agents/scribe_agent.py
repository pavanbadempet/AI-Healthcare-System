import json
import logging
from datetime import datetime

from sqlalchemy.orm import Session

from backend import models
from backend.agents.base_agent import BaseAgent
from backend.core_ai import generate
from backend.prompt_registry import get_prompt

logger = logging.getLogger(__name__)

class ClinicalScribeAgent(BaseAgent):
    """
    Agent that processes consultation transcripts and generates structured SOAP notes
    along with recommended clinical follow-up actions (medications, billing).
    """

    def __init__(self, db: Session, name: str = "Clinical Ambient Scribe"):
        super().__init__(name)
        self.db = db

    async def generate_soap_note(self, patient_id: int, transcript: str) -> dict:
        """
        Generates a structured SOAP note from consultation transcript.
        """
        self.start()

        # 1. Fetch patient
        self.log_step("Fetch Patient", f"Loading patient with ID: {patient_id}")
        patient = self.db.query(models.User).filter(
            models.User.id == patient_id,
            models.User.role == "patient"
        ).first()
        if not patient:
            self.log_error(f"Patient with ID {patient_id} not found")
            self.finish("failed")
            return {"error": "Patient not found"}

        # Calculate age
        age = "N/A"
        if patient.dob:
            try:
                dob_dt = datetime.strptime(patient.dob, "%Y-%m-%d") if isinstance(patient.dob, str) else patient.dob
                age = datetime.now().year - dob_dt.year
            except Exception:
                pass

        patient_context = (
            f"Patient Name: {patient.full_name or patient.username}\n"
            f"Age: {age}\n"
            f"Gender: {'Male' if patient.gender == 1 else 'Female' if patient.gender == 0 else 'Other'}\n"
        )

        self.log_step("Generate SOAP Note", "Calling Core AI Scribe Engine...")
        prompt = get_prompt("ambient_scribe_soap").format(
            patient_context=patient_context,
            transcript=transcript
        )
        self.estimate_tokens(prompt)
        raw_output = await generate(
            prompt=prompt,
            system="You are an expert clinical scribe trained to generate precise SOAP notes."
        )
        self.estimate_tokens(raw_output, is_output=True)

        try:
            # Clean raw output from any markdown block formatting
            clean_str = raw_output.strip()
            if clean_str.startswith("```json"):
                clean_str = clean_str[7:]
            if clean_str.endswith("```"):
                clean_str = clean_str[:-3]
            clean_str = clean_str.strip()

            structured_note = json.loads(clean_str)
            self.log_step("Parse JSON Response", "Successfully parsed structured SOAP JSON note.")
            self.finish("completed")
            return {
                "telemetry": {
                    "duration": self.duration,
                    "input_tokens": self.input_tokens_estimated,
                    "output_tokens": self.output_tokens_estimated,
                    "estimated_cost": self.estimated_cost
                },
                "data": structured_note
            }
        except Exception as e:
            logger.warning("Failed to parse scribe output as JSON: %s", e)
            self.log_error(f"JSON parsing failed: {str(e)}")
            # Fallback output
            fallback = {
                "subjective": "Failed to parse structured JSON note.",
                "objective": "Failed to parse structured JSON note.",
                "assessment": "Failed to parse structured JSON note.",
                "plan": f"Raw output: {raw_output}",
                "icd10_codes": [],
                "billing_codes": [],
                "prescriptions": [],
                "billing_items": []
            }
            self.finish("failed")
            return {
                "telemetry": {
                    "duration": self.duration,
                    "input_tokens": self.input_tokens_estimated,
                    "output_tokens": self.output_tokens_estimated,
                    "estimated_cost": self.estimated_cost
                },
                "data": fallback
            }
