import json
import logging
from datetime import datetime

from sqlalchemy.orm import Session

from backend import models
from backend.agents.base_agent import BaseAgent
from backend.core_ai import generate
from backend.prompt_registry import get_prompt

logger = logging.getLogger(__name__)

class ClinicalAdvisoryBoard(BaseAgent):
    """
    Coordinates the Multi-Agent Clinical Advisory Board.
    Orchestrates the 3-round sequential debate between Cardiologist, Endocrinologist,
    and GP Coordinator agents to synthesize a patient clinical consensus report.
    """

    def __init__(self, db: Session, name: str = "Clinical Advisory Board"):
        super().__init__(name)
        self.db = db

    async def execute_board(self, patient_id: int) -> dict:
        """
        Runs the multi-agent clinical advisory board debate.
        Returns:
            A structured dict containing debate transcript and final GP consensus note.
        """
        self.start()

        # 1. Fetch patient
        self.log_step("Fetch Patient Details", f"Loading demographics and clinical records for patient ID: {patient_id}")
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

        # 2. Fetch latest vital observation
        latest_vital = self.db.query(models.VitalObservation).filter(
            models.VitalObservation.patient_id == patient_id
        ).order_by(models.VitalObservation.observed_at.desc()).first()

        # 3. Fetch recent ML predictions from HealthRecord
        recent_records = self.db.query(models.HealthRecord).filter(
            models.HealthRecord.user_id == patient_id
        ).order_by(models.HealthRecord.timestamp.desc()).all()

        predictions_summary = []
        for r in recent_records:
            predictions_summary.append(f"- {r.record_type.title()} Prediction: {r.prediction} (Recorded: {r.timestamp.strftime('%Y-%m-%d')})")
        predictions_str = "\n".join(predictions_summary) if predictions_summary else "No recent ML risk predictions."

        # Construct patient clinical context
        patient_context = (
            f"Patient: {patient.full_name or patient.username}\n"
            f"Age: {age}\n"
            f"Gender: {'Male' if patient.gender == 1 else 'Female' if patient.gender == 0 else 'Other'}\n"
            f"Latest Vitals:\n"
            f"  - Heart Rate: {latest_vital.heart_rate if latest_vital else 72.0} bpm\n"
            f"  - Blood Pressure: {latest_vital.systolic_bp if latest_vital else 120.0}/{latest_vital.diastolic_bp if latest_vital else 80.0} mmHg\n"
            f"  - SpO2: {latest_vital.spo2 if latest_vital else 98.0}%\n"
            f"  - Temperature: {latest_vital.temperature_c if latest_vital else 36.8} C\n"
            f"Recent ML Disease Risk Predictions:\n{predictions_str}"
        )

        # --- Round 1: Initial Specialist Opinions ---
        self.log_step("Round 1: Cardiologist Analysis", "Generating cardiologist initial diagnostic assessment...")
        cardio_prompt = get_prompt("advisory_cardiologist_opinion").format(patient_context=patient_context)
        self.estimate_tokens(cardio_prompt)
        cardiologist_opinion = await generate(prompt=cardio_prompt, system="You are an expert clinical Cardiologist.")
        self.estimate_tokens(cardiologist_opinion, is_output=True)

        self.log_step("Round 1: Endocrinologist Analysis", "Generating endocrinologist initial diagnostic assessment...")
        endo_prompt = get_prompt("advisory_endocrinologist_opinion").format(patient_context=patient_context)
        self.estimate_tokens(endo_prompt)
        endocrinologist_opinion = await generate(prompt=endo_prompt, system="You are an expert clinical Endocrinologist.")
        self.estimate_tokens(endocrinologist_opinion, is_output=True)

        # --- Round 2: Cross-Consultation reviews ---
        self.log_step("Round 2: Cardiologist Cross-Consultation", "Cardiologist reviewing the endocrinology report...")
        cardio_rebuttal_prompt = get_prompt("advisory_cardiologist_rebuttal").format(
            patient_context=patient_context,
            own_opinion=cardiologist_opinion,
            colleague_opinion=endocrinologist_opinion
        )
        self.estimate_tokens(cardio_rebuttal_prompt)
        cardiologist_rebuttal = await generate(prompt=cardio_rebuttal_prompt, system="You are an expert clinical Cardiologist.")
        self.estimate_tokens(cardiologist_rebuttal, is_output=True)

        self.log_step("Round 2: Endocrinologist Cross-Consultation", "Endocrinologist reviewing the cardiology report...")
        endo_rebuttal_prompt = get_prompt("advisory_endocrinologist_rebuttal").format(
            patient_context=patient_context,
            own_opinion=endocrinologist_opinion,
            colleague_opinion=cardiologist_opinion
        )
        self.estimate_tokens(endo_rebuttal_prompt)
        endocrinologist_rebuttal = await generate(prompt=endo_rebuttal_prompt, system="You are an expert clinical Endocrinologist.")
        self.estimate_tokens(endocrinologist_rebuttal, is_output=True)

        # --- Round 3: GP Coordinator synthesis ---
        self.log_step("Round 3: GP Coordinator Synthesis", "Synthesizing clinical debate into structured clinical consensus report...")
        gp_prompt = get_prompt("advisory_gp_coordinator_synthesis").format(
            patient_context=patient_context,
            cardiologist_opinion=cardiologist_opinion,
            cardiologist_rebuttal=cardiologist_rebuttal,
            endocrinologist_opinion=endocrinologist_opinion,
            endocrinologist_rebuttal=endocrinologist_rebuttal
        )
        self.estimate_tokens(gp_prompt)
        gp_synthesis = await generate(prompt=gp_prompt, system="You are the General Practitioner Coordinator.")
        self.estimate_tokens(gp_synthesis, is_output=True)

        # Parse GP Synthesis JSON
        consensus_data = {
            "consensus_note": "A consensus could not be parsed dynamically. Please consult clinical notes.",
            "icd10_codes": [],
            "lifestyle_plan": [],
            "treatment_plan": []
        }
        try:
            cleaned = gp_synthesis.strip()
            if cleaned.startswith("```"):
                lines = cleaned.splitlines()
                if lines[0].startswith("```"):
                    lines = lines[1:]
                if lines[-1].startswith("```"):
                    lines = lines[:-1]
                cleaned = "\n".join(lines).strip()
            consensus_data = json.loads(cleaned)
        except Exception as ex:
            logger.warning("Advisory Board failed to parse GP synthesis JSON: %s. Raw content: %s", ex, gp_synthesis)
            consensus_data["consensus_note"] = gp_synthesis

        # Log high-priority CareEvent for auditability
        try:
            self.db.add(models.CareEvent(
                facility_id=patient.facility_id,
                patient_id=patient.id,
                event_type="advisory_board_consensus",
                title="Clinical Advisory Board Consensus",
                summary=(
                    f"Consensus: {consensus_data.get('consensus_note', '')[:100]}...\n"
                    f"ICD-10 Codes: {', '.join(consensus_data.get('icd10_codes', []))}"
                ),
                severity="info"
            ))
            self.db.commit()
        except Exception as ex:
            self.db.rollback()
            logger.error("Failed to log advisory board CareEvent: %s", ex)

        self.finish("completed")

        return {
            "status": "success",
            "patient_id": patient_id,
            "patient_vitals_context": f"HR: {latest_vital.heart_rate if latest_vital else 72.0} bpm, BP: {latest_vital.systolic_bp if latest_vital else 120.0}/{latest_vital.diastolic_bp if latest_vital else 80.0} mmHg",
            "debate": {
                "round1": {
                    "cardiologist": cardiologist_opinion,
                    "endocrinologist": endocrinologist_opinion
                },
                "round2": {
                    "cardiologist_rebuttal": cardiologist_rebuttal,
                    "endocrinologist_rebuttal": endocrinologist_rebuttal
                },
                "round3": {
                    "coordinator_synthesis": consensus_data
                }
            },
            "telemetry": {
                "duration_seconds": self.duration,
                "input_tokens": self.input_tokens_estimated,
                "output_tokens": self.output_tokens_estimated,
                "estimated_cost": self.estimated_cost
            }
        }
