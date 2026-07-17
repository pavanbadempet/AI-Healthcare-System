import json
import logging
from datetime import datetime

from sqlalchemy.orm import Session

from backend import models
from backend.agents.base_agent import BaseAgent
from backend.core_ai import generate
from backend.prompt_registry import get_prompt

logger = logging.getLogger(__name__)

class ClinicalNursingAgent(BaseAgent):
    """
    State-of-the-Art (SOTA) Nursing Care Coordinator & Handoff Agent.
    Evaluates telemetry status, vital trends, and alerts to compile handover summaries
    and prioritize shift-specific care coordination tasks.
    """

    def __init__(self, db: Session, name: str = "Clinical Nursing Coordinator"):
        super().__init__(name)
        self.db = db

    async def generate_handoff_card(self, patient_id: int) -> dict:
        """
        Processes vital trends and active alerts to synthesize a nurse shift handoff card.
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
            f"Existing Conditions: {patient.existing_ailments or 'None recorded'}\n"
        )

        # 2. Fetch vital trends (last 24 hours)
        self.log_step("Fetch Vital Trends", f"Querying 24h telemetry trend for patient: {patient_id}")
        vitals = self.db.query(models.VitalObservation).filter(
            models.VitalObservation.patient_id == patient_id
        ).order_by(models.VitalObservation.observed_at.desc()).limit(8).all()

        vitals_list = []
        for v in vitals:
            vitals_list.append(
                f"Heart Rate: {v.heart_rate} bpm, BP: {v.systolic_bp}/{v.diastolic_bp} mmHg, Temp: {v.temperature_c}°C"
            )
        vital_trends = "\n".join(vitals_list) if vitals_list else "No telemetry data recorded."

        # 3. Fetch active telemetry alerts
        self.log_step("Fetch Telemetry Alerts", f"Querying active monitoring signals for patient: {patient_id}")
        alerts = self.db.query(models.MonitoringSignal).filter(
            models.MonitoringSignal.patient_id == patient_id
        ).order_by(models.MonitoringSignal.created_at.desc()).limit(5).all()

        alerts_list = []
        for a in alerts:
            alerts_list.append(f"[{a.severity.upper()}] {a.signal_type.title()}: {a.message}")
        active_alerts = "\n".join(alerts_list) if alerts_list else "No active alerts or telemetry warnings."

        # 4. Generate Handoff Card
        self.log_step("Synthesize Handoff Card", "Calling SOTA Nursing Coordinator LLM...")
        prompt = get_prompt("clinical_nursing_handoff").format(
            patient_context=patient_context,
            vital_trends=vital_trends,
            active_alerts=active_alerts
        )
        self.estimate_tokens(prompt)
        raw_output = await generate(
            prompt=prompt,
            system="You are an expert charge nurse skilled in generating structured shift handover cards and prioritizing patient safety duties."
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

            structured_handoff = json.loads(clean_str)
            self.log_step("Parse JSON Response", "Successfully parsed structured nursing handoff card.")
            self.finish("completed")
            return {
                "telemetry": {
                    "duration": self.duration,
                    "input_tokens": self.input_tokens_estimated,
                    "output_tokens": self.output_tokens_estimated,
                    "estimated_cost": self.estimated_cost
                },
                "data": structured_handoff
            }
        except Exception as e:
            logger.warning("Failed to parse nursing handoff output as JSON: %s", e)
            self.log_error(f"JSON parsing failed: {str(e)}")
            fallback = {
                "handoff_summary": "Failed to compile nursing handoff card.",
                "priority_tasks": ["Initiate standard monitoring protocol.", "Verify patient details manually."],
                "monitoring_frequency": "Standard ward protocol (e.g. Q4h)",
                "safety_concerns": ["Review vitals manually; model output was not valid JSON."]
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
