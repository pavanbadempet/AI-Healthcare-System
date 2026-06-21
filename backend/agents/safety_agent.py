import json
import logging

from sqlalchemy.orm import Session

from backend import models
from backend.agents.base_agent import BaseAgent
from backend.core_ai import generate
from backend.prompt_registry import get_prompt

logger = logging.getLogger(__name__)

class PrescribingSafetyAgent(BaseAgent):
    """
    Agent that checks drug safety contraindications and interactions.
    """

    def __init__(self, db: Session, name: str = "Prescribing Safety Engine"):
        super().__init__(name)
        self.db = db

    async def check_prescription_safety(
        self,
        patient_id: int,
        medication_name: str,
        dosage: str,
        frequency: str,
        duration: str,
        additional_allergies: list[str] | None = None
    ) -> dict:
        """
        Runs the drug compatibility check.
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

        # 2. Fetch active prescriptions
        self.log_step("Fetch Active Prescriptions", "Retrieving patient's current active medications")
        active_prescripts = self.db.query(models.Prescription).filter(
            models.Prescription.patient_id == patient_id,
            models.Prescription.status == "active"
        ).all()

        current_meds = []
        for p in active_prescripts:
            for item in p.items:
                if item.status in ["pending", "dispensed", "partially_dispensed"]:
                    current_meds.append(f"{item.medication_name} ({item.dosage}, {item.frequency})")

        active_meds_str = ", ".join(current_meds) if current_meds else "None"

        # 3. Fetch active conditions
        active_conditions = patient.existing_ailments or "No chronic ailments recorded"

        # 4. Determine allergies
        allergies_list = additional_allergies or []
        # Parse patient about_me/ailments for mentions of allergy
        for text in [patient.about_me, patient.existing_ailments]:
            if text:
                for line in text.split("\n"):
                    if "allergy" in line.lower() or "allergic" in line.lower():
                        allergies_list.append(line.strip())

        allergies_str = ", ".join(allergies_list) if allergies_list else "No known drug allergies"

        # 5. Fetch recent ML risk predictions
        recent_records = self.db.query(models.HealthRecord).filter(
            models.HealthRecord.user_id == patient_id
        ).order_by(models.HealthRecord.timestamp.desc()).all()

        predictions_summary = []
        for r in recent_records:
            predictions_summary.append(f"{r.record_type.title()}: {r.prediction}")
        ml_risks_str = ", ".join(predictions_summary) if predictions_summary else "No recent ML predictions"

        # 6. Generate safety check
        self.log_step("Analyze Safety", "Calling pharmacist safety auditor LLM...")
        prompt = get_prompt("drug_safety_check").format(
            active_medications=active_meds_str,
            active_conditions=active_conditions,
            allergies=allergies_str,
            ml_risks=ml_risks_str,
            medication_name=medication_name,
            dosage=dosage,
            frequency=frequency,
            duration=duration
        )
        self.estimate_tokens(prompt)
        raw_output = await generate(
            prompt=prompt,
            system="You are an expert clinical pharmacist safety auditor."
        )
        self.estimate_tokens(raw_output, is_output=True)

        try:
            # Clean raw output
            clean_str = raw_output.strip()
            if clean_str.startswith("```json"):
                clean_str = clean_str[7:]
            if clean_str.endswith("```"):
                clean_str = clean_str[:-3]
            clean_str = clean_str.strip()

            parsed = json.loads(clean_str)
            self.log_step("Parse Alerts JSON", "Successfully parsed interaction alerts.")
            self.finish("completed")
            return {
                "telemetry": {
                    "duration": self.duration,
                    "input_tokens": self.input_tokens_estimated,
                    "output_tokens": self.output_tokens_estimated,
                    "estimated_cost": self.estimated_cost
                },
                "alerts": parsed.get("alerts", [])
            }
        except Exception as e:
            logger.warning("Failed to parse drug safety output as JSON: %s", e)
            self.log_error(f"JSON parsing failed: {str(e)}")
            fallback = {
                "telemetry": {
                    "duration": self.duration,
                    "input_tokens": self.input_tokens_estimated,
                    "output_tokens": self.output_tokens_estimated,
                    "estimated_cost": self.estimated_cost
                },
                "alerts": [
                    {
                        "type": "error",
                        "severity": "info",
                        "message": "Prescribing safety audit fallback: could not verify safety due to parsing error.",
                        "evidence": f"Raw output: {raw_output}"
                    }
                ]
            }
            self.finish("failed")
            return fallback
