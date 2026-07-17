import json
import logging
from datetime import datetime

from sqlalchemy.orm import Session

from backend import models
from backend.agents.base_agent import BaseAgent
from backend.core_ai import generate
from backend.prompt_registry import get_prompt

logger = logging.getLogger(__name__)

class ClinicalDischargeAgent(BaseAgent):
    """
    State-of-the-Art (SOTA) Patient Discharge Summary & Transition-of-Care Agent.
    Reviews recent vitals, predictions, and demographics to generate a transition plan,
    patient instructions, and professional discharge summary.
    """

    def __init__(self, db: Session, name: str = "Clinical Discharge Coordinator"):
        super().__init__(name)
        self.db = db

    async def generate_discharge_plan(self, patient_id: int) -> dict:
        """
        Gathers patient stats, vitals, and predictions to synthesize a discharge summary plan.
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

        # Map gender string representation safely
        gender_val = "Other"
        if patient.gender:
            norm_gender = str(patient.gender).strip().lower()
            if norm_gender in ("1", "male", "m"):
                gender_val = "Male"
            elif norm_gender in ("0", "female", "f"):
                gender_val = "Female"
            else:
                gender_val = patient.gender.capitalize()

        patient_context = (
            f"Patient Name: {patient.full_name or patient.username}\n"
            f"Age: {age}\n"
            f"Gender: {gender_val}\n"
            f"Existing Conditions: {patient.existing_ailments or 'None recorded'}\n"
        )

        # 2. Fetch recent vitals
        self.log_step("Fetch Vitals", f"Querying vital logs for patient: {patient_id}")
        vitals = self.db.query(models.VitalObservation).filter(
            models.VitalObservation.patient_id == patient_id
        ).order_by(models.VitalObservation.observed_at.desc()).limit(5).all()

        vitals_list = []
        for v in vitals:
            vitals_list.append(
                f"[{v.observed_at.strftime('%Y-%m-%d %H:%M') if v.observed_at else 'Unknown'}] "
                f"Heart Rate: {v.heart_rate} bpm, BP: {v.systolic_bp}/{v.diastolic_bp} mmHg, Temp: {v.temperature_c}°C"
            )
        vitals_history = "\n".join(vitals_list) if vitals_list else "No recent vitals recorded."

        # 3. Fetch recent ML predictions
        self.log_step("Fetch ML Predictions", f"Querying risk assessments for patient: {patient_id}")
        predictions = self.db.query(models.HealthRecord).filter(
            models.HealthRecord.user_id == patient_id
        ).order_by(models.HealthRecord.timestamp.desc()).limit(3).all()

        preds_list = []
        for p in predictions:
            preds_list.append(f"{p.record_type.title()}: {p.prediction} (Logged: {p.timestamp.strftime('%Y-%m-%d') if p.timestamp else 'Unknown'})")
        predictions_summary = "\n".join(preds_list) if preds_list else "No recent ML risk assessments."

        # 4. Generate Discharge Summary
        self.log_step("Synthesize Discharge Plan", "Calling SOTA Discharge Coordinator LLM...")
        prompt = get_prompt("clinical_discharge_summary").format(
            patient_context=patient_context,
            vitals_history=vitals_history,
            predictions_summary=predictions_summary
        )
        self.estimate_tokens(prompt)
        raw_output = await generate(
            prompt=prompt,
            system="You are an expert chief clinical discharge coordinator skilled in organizing transition-of-care summaries and patient-friendly guidance."
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

            structured_discharge = json.loads(clean_str)
            self.log_step("Parse JSON Response", "Successfully parsed structured discharge summary.")
            self.finish("completed")
            return {
                "telemetry": {
                    "duration": self.duration,
                    "input_tokens": self.input_tokens_estimated,
                    "output_tokens": self.output_tokens_estimated,
                    "estimated_cost": self.estimated_cost
                },
                "data": structured_discharge
            }
        except Exception as e:
            logger.warning("Failed to parse discharge summary output as JSON: %s", e)
            self.log_error(f"JSON parsing failed: {str(e)}")
            fallback = {
                "discharge_summary": "Failed to generate discharge summary.",
                "transition_plan": ["Contact primary physician as soon as possible."],
                "patient_instructions": f"Raw summary: {raw_output}",
                "follow_up_appointments": "Consult medical provider within 7 days."
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
