import logging
import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import or_
from sqlalchemy.orm import Session

from .. import core_ai, email_service, fhir, models, rag
from ..facility_scope import users_share_facility_context
from ..model_service import model_service
from ..prompt_registry import get_prompt

logger = logging.getLogger(__name__)

# Pattern to capture booking action tags: [BOOKING_ACTION: doctor_id=X, date=YYYY-MM-DD, time=HH:MM, reason=text]
BOOKING_ACTION_PATTERN = re.compile(
    r"\[BOOKING_ACTION:\s*doctor_id=(\d+),\s*date=([\d\-]+),\s*time=([\d\:]+),\s*reason=(.*?)\]",
    re.IGNORECASE
)

# Symptoms keywords for routing / triage warnings
EMERGENCY_KEYWORDS = ["chest pain", "breathing difficulty", "shortness of breath", "stroke", "numbness", "severe bleeding", "unconscious"]
CLINICAL_SPECIALTIES_MAP = {
    "heart": "Cardiologist",
    "cardiac": "Cardiologist",
    "diabetes": "Diabetologist",
    "glucose": "Diabetologist",
    "liver": "Hepatologist",
    "kidney": "Nephrologist",
    "renal": "Nephrologist",
    "lung": "Pulmonologist",
    "lungs": "Pulmonologist"
}

class SchedulingAgent:
    """
    Clinical-Aware Scheduling Agent (CASA).
    Manages conversational appointment scheduling, checks for clinical urgency,
    recommends specialties based on symptoms, and executes bookings in the database.
    """

    def __init__(self, db: Session, user: models.User):
        self.db = db
        self.user = user

    def _get_doctor_directory_string(self) -> str:
        """Fetch all doctors available to the patient's facility scope and format as a directory."""
        query = self.db.query(models.User).filter(models.User.role == "doctor")
        if self.user.facility_id is not None:
            query = query.filter(
                or_(
                    models.User.facility_id == self.user.facility_id,
                    models.User.facility_id.is_(None)
                )
            )
        doctors = query.all()

        dir_lines = []
        for doc in doctors:
            spec = doc.specialization or "General Physician"
            fee = doc.consultation_fee or 500.0
            dir_lines.append(f"- ID: {doc.id} | Name: {doc.full_name or doc.username} | Specialty: {spec} | Fee: Rs.{fee}")

        if not dir_lines:
            return "No doctors currently available."
        return "\n".join(dir_lines)

    def _check_symptoms(self, message: str) -> Tuple[Optional[str], List[str]]:
        """
        Check if message contains emergency or specialty-specific keywords.
        Returns:
            A tuple of (warning_message, detected_areas)
        """
        msg_lower = message.lower()

        # 1. Emergency Check
        detected_emergencies = [kw for kw in EMERGENCY_KEYWORDS if kw in msg_lower]
        if detected_emergencies:
            kw_list = ", ".join(detected_emergencies)
            return (
                f"⚠️ **EMERGENCY WARNING:** The symptoms you described ({kw_list}) may require immediate medical attention. "
                "Please call emergency services (e.g., 112 or 911) or visit the nearest emergency room immediately.",
                []
            )

        # 2. Specialty Matching
        detected_areas = []
        for kw, spec in CLINICAL_SPECIALTIES_MAP.items():
            if kw in msg_lower:
                detected_areas.append(spec)

        if detected_areas:
            spec_list = ", ".join(set(detected_areas))
            return (
                f"💡 **Clinical Suggestion:** Based on the symptoms you mentioned, we recommend booking with a **{spec_list}**. "
                "Please note that our local ML risk assessment forms can also help evaluate your symptoms.",
                detected_areas
            )

        return None, []

    def _get_contributing_factors(self, model_name: str, data: Any) -> List[str]:
        """Identify top contributing risk factors based on inputs."""
        factors = []
        if model_name == "diabetes":
            if getattr(data, "hypertension", 0) == 1:
                factors.append("Hypertension")
            if getattr(data, "high_chol", 0) == 1:
                factors.append("High Cholesterol")
            if getattr(data, "bmi", 25.0) >= 30.0:
                factors.append(f"Obesity (BMI: {data.bmi:.1f})")
            if getattr(data, "smoking_history", 0) == 1:
                factors.append("Smoking History")
        elif model_name == "heart":
            if getattr(data, "trestbps", 120.0) >= 140.0:
                factors.append(f"Elevated Rest BP ({data.trestbps} mmHg)")
            if getattr(data, "chol", 200.0) >= 240.0:
                factors.append(f"High Cholesterol ({data.chol} mg/dl)")
            if getattr(data, "thalach", 80.0) > 100.0 or getattr(data, "thalach", 80.0) < 60.0:
                factors.append(f"Abnormal Max Heart Rate ({data.thalach} bpm)")
            if getattr(data, "exang", 0) == 1:
                factors.append("Exercise Induced Angina")
        elif model_name == "lungs":
            if getattr(data, "shortness_of_breath", 0) == 1:
                factors.append("Shortness of Breath")
            if getattr(data, "smoking", 0) == 1:
                factors.append("Smoking")
            if getattr(data, "coughing", 0) == 1:
                factors.append("Chronic Coughing")
        elif model_name == "kidney":
            if getattr(data, "bp", 120.0) >= 140.0:
                factors.append(f"Elevated BP ({data.bp} mmHg)")
        elif model_name == "liver":
            if getattr(data, "age", 35.0) >= 60.0:
                factors.append(f"Senior Age ({data.age:.1f})")
        return factors

    def _run_clinical_screening(self, specialty: str) -> Optional[Dict[str, Any]]:
        """
        Run local ML risk classification matching the doctor's specialty.
        Returns a dict of prediction results or None.
        """
        spec_lower = specialty.lower()
        model_name = None
        if "cardi" in spec_lower:
            model_name = "heart"
        elif "diabet" in spec_lower or "endo" in spec_lower:
            model_name = "diabetes"
        elif "nephr" in spec_lower or "renal" in spec_lower:
            model_name = "kidney"
        elif "hepat" in spec_lower or "liver" in spec_lower:
            model_name = "liver"
        elif "pulmon" in spec_lower or "lung" in spec_lower or "respir" in spec_lower:
            model_name = "lungs"

        if not model_name or not model_service.is_available(model_name):
            return None

        # 1. Gather patient demographics
        age = 35.0
        if self.user.dob:
            try:
                dob_dt = datetime.strptime(self.user.dob.strip(), "%Y-%m-%d")
                age = (datetime.now() - dob_dt).days / 365.25
            except Exception:
                pass

        gender = 1 if self.user.gender and self.user.gender.lower() in ("male", "m", "1") else 0

        # 2. Gather latest vitals
        latest_vital = self.db.query(models.VitalObservation).filter(
            models.VitalObservation.patient_id == self.user.id
        ).order_by(models.VitalObservation.observed_at.desc()).first()

        heart_rate = latest_vital.heart_rate if latest_vital else None
        systolic_bp = latest_vital.systolic_bp if latest_vital else None
        diastolic_bp = latest_vital.diastolic_bp if latest_vital else None
        spo2 = latest_vital.spo2 if latest_vital else None

        bmi = None
        if self.user.height and self.user.weight:
            try:
                height_m = self.user.height / 100.0
                bmi = self.user.weight / (height_m ** 2)
            except Exception:
                pass

        # 3. Call corresponding prediction schema & service method
        try:
            from ..schemas import prediction as pred_schemas

            if model_name == "diabetes":
                data = pred_schemas.DiabetesInput(
                    gender=gender,
                    age=age,
                    hypertension=1 if (systolic_bp and systolic_bp >= 140) or (diastolic_bp and diastolic_bp >= 90) else 0,
                    heart_disease=0,
                    smoking_history=0,
                    bmi=bmi or 25.0,
                    high_chol=0,
                    physical_activity=1,
                    general_health=3
                )
                res = model_service.predict_diabetes(data)
            elif model_name == "heart":
                data = pred_schemas.HeartInput(
                    age=age,
                    sex=gender,
                    cp=0,
                    trestbps=systolic_bp or 120.0,
                    chol=200.0,
                    fbs=0,
                    restecg=0,
                    thalach=heart_rate or 80.0,
                    exang=0,
                    oldpeak=0.0,
                    slope=1,
                    ca=0,
                    thal=2
                )
                res = model_service.predict_heart(data)
            elif model_name == "lungs":
                data = pred_schemas.LungInput(
                    gender=gender,
                    age=age,
                    smoking=0,
                    yellow_fingers=0,
                    anxiety=0,
                    peer_pressure=0,
                    chronic_disease=0,
                    fatigue=0,
                    allergy=0,
                    wheezing=0,
                    alcohol=0,
                    coughing=0,
                    shortness_of_breath=1 if (spo2 and spo2 < 95) else 0,
                    swallowing_difficulty=0,
                    chest_pain=0
                )
                res = model_service.predict_lungs(data)
            elif model_name == "kidney":
                data = pred_schemas.KidneyInput(
                    age=age,
                    bp=systolic_bp or 120.0,
                    gender=gender
                )
                res = model_service.predict_kidney(data)
            elif model_name == "liver":
                data = pred_schemas.LiverInput(
                    age=age,
                    gender=gender
                )
                res = model_service.predict_liver(data)
            else:
                return None

            factors = self._get_contributing_factors(model_name, data)
            return {
                "model_name": model_name,
                "prediction": res.prediction,
                "confidence": res.confidence,
                "risk_level": res.risk_level,
                "input_data": data.model_dump(),
                "contributing_factors": factors
            }
        except Exception as e:
            logger.warning("Clinical pre-screening model prediction failed: %s", e)
            return None

    async def chat(self, message: str, history: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        Processes a multi-turn chat message, generates the agent response,
        and triggers a booking action if finalized.
        """
        # 0. Check if patient is authorizing ABDM consent
        from datetime import timedelta
        msg_lower = message.lower()
        if any(kw in msg_lower for kw in ("authorize consent", "yes, request consent", "yes, please request consent", "approve consent")):
            existing_consent = self.db.query(models.InteroperabilityConsent).filter(
                models.InteroperabilityConsent.patient_id == self.user.id,
                models.InteroperabilityConsent.status == "active"
            ).first()
            if not existing_consent:
                new_consent = models.InteroperabilityConsent(
                    facility_id=self.user.facility_id,
                    patient_id=self.user.id,
                    scope="fhir_bundle_export",
                    purpose="Clinical RAG Context retrieval during appointment booking",
                    recipient_type="care_team",
                    status="active",
                    expires_at=datetime.utcnow() + timedelta(days=365)
                )
                self.db.add(new_consent)
                self.db.commit()
                # Run pre-fetch immediately to warm cache
                self.prefetch_and_index_history()

        # Pre-check symptoms for warnings
        warning, _ = self._check_symptoms(message)

        # Build prompt using standards-based pre-fetching
        system_prompt = self.get_system_prompt()

        # Format history and current prompt for LLM
        llm_messages = []
        for h in history:
            role = "User" if h["role"] == "user" else "AI"
            llm_messages.append(f"{role}: {h['content']}")
        llm_messages.append(f"User: {message}")

        full_prompt = system_prompt + "\n\n" + "\n\n".join(llm_messages) + "\n\nAI:"

        # Generate response using multi-tier core_ai
        raw_reply = await core_ai.generate(full_prompt)
        if not raw_reply:
            raw_reply = "AI is temporarily unavailable. Please try again shortly."

        # Scan for booking action
        booking_match = BOOKING_ACTION_PATTERN.search(raw_reply)
        action_triggered = False
        booking_details = None
        error_msg = None

        if booking_match:
            action_triggered = True
            doc_id_str, date_str, time_str, reason_str = booking_match.groups()

            # Attempt database write-back
            try:
                doc_id = int(doc_id_str)
                # Parse date & time
                dt_str = f"{date_str} {time_str}"
                appointment_dt = None
                for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"):
                    try:
                        appointment_dt = datetime.strptime(dt_str, fmt)
                        break
                    except ValueError:
                        continue

                if not appointment_dt:
                    raise ValueError("Invalid date/time format")

                # Verify future date
                if appointment_dt <= datetime.now():
                    raise ValueError("Appointment time must be in the future")

                # Verify doctor existence
                doctor = self.db.query(models.User).filter(
                    models.User.id == doc_id,
                    models.User.role == "doctor"
                ).first()

                if not doctor:
                    raise ValueError(f"Doctor with ID {doc_id} not found")

                # Check facility context
                if not users_share_facility_context(self.db, self.user.id, doctor.id):
                    raise ValueError("Doctor does not belong to your clinical facility scope")

                # Check doctor slot availability
                existing = self.db.query(models.Appointment).filter(
                    models.Appointment.doctor_id == doc_id,
                    models.Appointment.date_time == appointment_dt,
                    models.Appointment.status.in_(("Scheduled", "Rescheduled"))
                ).first()
                if existing:
                    raise ValueError("The doctor is already booked at that specific date and time")

                # Run pre-screening
                spec = doctor.specialization or "General Physician"
                screen_res = self._run_clinical_screening(spec)
                final_reason = reason_str.strip()
                is_high_risk = False

                if screen_res:
                    risk_level = screen_res.get("risk_level", "Low")
                    risk_desc = f"{screen_res['model_name'].title()} {risk_level} Risk ({screen_res['confidence']}%)"
                    factors = screen_res.get("contributing_factors", [])
                    factors_str = f" | Risk Factors: {', '.join(factors)}" if factors else ""

                    if risk_level.strip().lower() in ("high", "high risk"):
                        is_high_risk = True
                        brief = f"🚨 [URGENT CLINICAL TRIAGE] [AI Risk Screen: {risk_desc}{factors_str}]"
                    else:
                        brief = f"[AI Risk Screen: {risk_desc}{factors_str}]"
                    final_reason = f"{brief} {final_reason}"

                # Create appointment
                new_appt = models.Appointment(
                    facility_id=doctor.facility_id or self.user.facility_id,
                    user_id=self.user.id,
                    doctor_id=doctor.id,
                    specialist=spec,
                    date_time=appointment_dt,
                    reason=final_reason,
                    status="Scheduled"
                )
                self.db.add(new_appt)

                if screen_res:
                    import json
                    db_record = models.HealthRecord(
                        user_id=self.user.id,
                        record_type=screen_res["model_name"],
                        data=json.dumps(screen_res.get("input_data", {})),
                        prediction=f"{screen_res['risk_level']} Risk ({screen_res['confidence']}"
                    )
                    self.db.add(db_record)

                    if is_high_risk:
                        # Log high-priority CareEvent for clinical nurse alert
                        new_event = models.CareEvent(
                            facility_id=doctor.facility_id or self.user.facility_id,
                            patient_id=self.user.id,
                            event_type="triage_escalation",
                            title=f"🚨 High Risk Triage Escalation ({screen_res['model_name'].title()})",
                            summary=f"Scheduling screening flagged patient as High Risk. Contributing factors: {', '.join(factors)}.",
                            severity="high"
                        )
                        self.db.add(new_event)

                self.db.commit()
                self.db.refresh(new_appt)

                # Send confirmation email
                try:
                    video_link = f"https://meet.jit.si/ai-health-{new_appt.id}"
                    email_service.send_booking_confirmation(
                        to_email=self.user.email or "patient@example.com",
                        patient_name=self.user.full_name or self.user.username,
                        doctor_name=doctor.full_name or doctor.username,
                        date_time=dt_str,
                        link=video_link
                    )
                except Exception as e:
                    logger.warning("Failed to send email confirmation: %s", e)

                booking_details = {
                    "id": new_appt.id,
                    "doctor_name": doctor.full_name or doctor.username,
                    "specialist": doctor.specialization or "General Physician",
                    "date_time": new_appt.date_time.isoformat(),
                    "reason": new_appt.reason
                }

                # Replace the raw action tag in the response with a clean confirmation
                clean_msg = f"CONFIRMED: Your appointment has been booked with {doctor.full_name or doctor.username} on {date_str} at {time_str}."
                raw_reply = BOOKING_ACTION_PATTERN.sub(clean_msg, raw_reply)

            except Exception as ex:
                self.db.rollback()
                error_msg = str(ex)
                logger.error("CASA failed to book appointment: %s", ex)
                # Replace tag with error details
                raw_reply = BOOKING_ACTION_PATTERN.sub(f"\n[Booking failed: {error_msg}. Please try scheduling again.]", raw_reply)

        # Prepend symptoms warning if applicable
        final_reply = raw_reply
        if warning:
            final_reply = f"{warning}\n\n{raw_reply}"

        return {
            "response": final_reply,
            "action_triggered": action_triggered,
            "booking_details": booking_details,
            "error": error_msg
        }

    def _prefetch_patient_history_bundle(self) -> dict:
        """
        Queries all database records (vitals, diagnostics, past encounters, prescriptions)
        for the patient, maps them to FHIR resources and constructs a unified FHIR bundle.
        """
        resources = [fhir.patient_resource(self.user)]

        # 1. Encounters
        encounters = self.db.query(models.Encounter).filter(
            models.Encounter.patient_id == self.user.id
        ).all()
        for enc in encounters:
            resources.append(fhir.encounter_resource(enc, self.user.id))

        # 2. Observations
        observations = self.db.query(models.VitalObservation).filter(
            models.VitalObservation.patient_id == self.user.id
        ).all()
        for obs in observations:
            resources.append(fhir.observation_resource(obs, self.user.id))

        # 3. DiagnosticReports
        diagnostic_results = self.db.query(models.DiagnosticResult).filter(
            models.DiagnosticResult.patient_id == self.user.id
        ).all()
        for result in diagnostic_results:
            resources.append(fhir.diagnostic_report_resource(result, self.user.id))

        # 4. MedicationRequests (Prescriptions)
        prescriptions = self.db.query(models.Prescription).filter(
            models.Prescription.patient_id == self.user.id
        ).all()
        for prescription in prescriptions:
            resources.append(fhir.medication_request_resource(prescription, self.user.id))

        # 5. Invoices
        invoices = self.db.query(models.Invoice).filter(
            models.Invoice.patient_id == self.user.id
        ).all()
        for invoice in invoices:
            resources.append(fhir.invoice_resource(invoice, self.user.id))

        # 6. CareEvents
        care_events = self.db.query(models.CareEvent).filter(
            models.CareEvent.patient_id == self.user.id
        ).all()
        for event in care_events:
            resources.append(fhir.care_event_resource(event, self.user.id))

        return fhir.build_bundle(resources, timestamp=datetime.now())

    def _serialize_bundle_to_summary(self, bundle: dict) -> str:
        """
        Converts the FHIR R4 Bundle into a patient-anonymized, readable clinical text summary.
        Does not include patient name or exact DOB to protect PII.
        """
        entries = bundle.get("entry", [])
        if not entries:
            return "No historical clinical records found."

        summary_parts = ["FHIR Bundle Patient History Summary:"]

        for entry in entries:
            res = entry.get("resource", {})
            res_type = res.get("resourceType")
            res_id = res.get("id")

            if res_type == "Patient":
                gender = res.get("gender", "unknown")
                summary_parts.append(f"Patient ID: {res_id}\nGender: {gender}")

            elif res_type == "Encounter":
                status = res.get("status", "unknown")
                class_code = res.get("class", {}).get("code", "unknown")
                period = res.get("period", {})
                start = period.get("start", "unknown")
                end = period.get("end", "unknown")
                summary_parts.append(
                    f"Resource: Encounter/{res_id}\n"
                    f"Status: {status}\n"
                    f"Class: {class_code}\n"
                    f"Period: {start} to {end}"
                )

            elif res_type == "Observation":
                status = res.get("status", "unknown")
                obs_date = res.get("effectiveDateTime", "unknown")
                components = res.get("component", [])
                vitals_str = []
                for comp in components:
                    display = comp.get("code", {}).get("text", "Vital Sign")
                    val_qty = comp.get("valueQuantity", {})
                    val = val_qty.get("value")
                    unit = val_qty.get("unit", "")
                    if val is not None:
                        vitals_str.append(f"- {display}: {val} {unit}")

                vitals_text = "\n".join(vitals_str) if vitals_str else "- No vitals recorded"
                summary_parts.append(
                    f"Resource: Observation/{res_id}\n"
                    f"Status: {status}\n"
                    f"Observed: {obs_date}\n"
                    f"Vitals:\n{vitals_text}"
                )

            elif res_type == "DiagnosticReport":
                status = res.get("status", "unknown")
                code_text = res.get("code", {}).get("text", "Diagnostic Result")
                conclusion = res.get("conclusion", "No conclusion provided")
                issued = res.get("issued", "unknown")
                summary_parts.append(
                    f"Resource: DiagnosticReport/{res_id}\n"
                    f"Status: {status}\n"
                    f"Test: {code_text}\n"
                    f"Conclusion: {conclusion}\n"
                    f"Issued: {issued}"
                )

            elif res_type == "MedicationRequest":
                status = res.get("status", "unknown")
                med_text = res.get("medicationCodeableConcept", {}).get("text", "Medication")
                authored = res.get("authoredOn", "unknown")
                dosages = res.get("dosageInstruction", [])
                dosage_parts = []
                for d in dosages:
                    if d.get("text"):
                        dosage_parts.append(d.get("text"))
                dosage_text = "; ".join(dosage_parts) if dosage_parts else "No specific instructions"

                summary_parts.append(
                    f"Resource: MedicationRequest/{res_id}\n"
                    f"Status: {status}\n"
                    f"Medication: {med_text}\n"
                    f"Instructions: {dosage_text}\n"
                    f"Authored On: {authored}"
                )

            elif res_type == "Invoice":
                status = res.get("status", "unknown")
                total_net = res.get("totalNet", {})
                total = total_net.get("value", "0.0")
                curr = total_net.get("currency", "INR")
                date_val = res.get("date", "unknown")
                summary_parts.append(
                    f"Resource: Invoice/{res_id}\n"
                    f"Status: {status}\n"
                    f"Total Net Amount: {total} {curr}\n"
                    f"Date: {date_val}"
                )

            elif res_type == "CareEvent":
                status = res.get("status", "unknown")
                code_text = res.get("code", {}).get("text", "Care Event")
                title = res.get("title", "No Title")
                severity = res.get("severity", "routine")
                recorded = res.get("recorded", "unknown")
                summary_parts.append(
                    f"Resource: CareEvent/{res_id}\n"
                    f"Status: {status}\n"
                    f"Type: {code_text}\n"
                    f"Title: {title}\n"
                    f"Severity: {severity}\n"
                    f"Recorded: {recorded}"
                )

        return "\n\n".join(summary_parts)

    def has_active_abdm_consent(self) -> bool:
        """Check if patient has an active interoperability consent."""
        consent = self.db.query(models.InteroperabilityConsent).filter(
            models.InteroperabilityConsent.patient_id == self.user.id,
            models.InteroperabilityConsent.status == "active"
        ).first()
        return consent is not None

    def prefetch_and_index_history(self) -> None:
        """
        Pre-fetches clinical records, builds the FHIR bundle, and indexes the
        serialized summary in the RAG vector store using patient-scoped metadata.
        Only runs if active ABDM consent exists.
        """
        if not self.has_active_abdm_consent():
            logger.warning("ABDM Consent is missing or inactive for user ID %s. Bypassing history pre-fetching.", self.user.id)
            return

        try:
            bundle = self._prefetch_patient_history_bundle()
            summary_text = self._serialize_bundle_to_summary(bundle)

            # Index into RAG vector store
            record_id = f"fhir_bundle_summary_{self.user.id}"
            metadata = {
                "user_id": str(self.user.id),
                "type": "fhir_bundle_summary",
                "timestamp": datetime.now().isoformat()
            }
            if self.user.facility_id is not None:
                metadata["facility_id"] = str(self.user.facility_id)

            rag.get_vector_store().add(summary_text, metadata, record_id)
            logger.info("Successfully pre-fetched and indexed FHIR bundle summary in RAG for user ID %s", self.user.id)
        except Exception as e:
            logger.error("Failed to prefetch and index patient clinical history in RAG: %s", e)

    def get_system_prompt(self) -> str:
        """
        Pre-fetches and indexes patient history, retrieves the history from RAG,
        and returns the formatted scheduling system prompt.
        """
        # 1. Index updated history
        self.prefetch_and_index_history()

        # 2. Retrieve context from RAG
        history_chunks = []
        if self.has_active_abdm_consent():
            try:
                history_chunks = rag.search_similar_records(
                    user_id=str(self.user.id),
                    query="FHIR Bundle Patient History Summary",
                    n_results=3,
                    facility_id=str(self.user.facility_id) if self.user.facility_id is not None else None
                )
            except Exception as e:
                logger.warning("Failed to retrieve patient history from RAG: %s", e)

        patient_history = "\n\n".join(history_chunks) if history_chunks else "No patient historical clinical records found."

        # If consent is missing, append instructions to prompt the user
        consent_instruction = ""
        if not self.has_active_abdm_consent():
            consent_instruction = (
                "\n\nIMPORTANT: The patient's ABDM Interoperability Consent is currently INACTIVE/MISSING. "
                "You MUST ask the patient to authorize/grant consent before continuing with booking or pre-fetching. "
                "Explicitly output this question to the patient: 'I see you do not have an active ABDM Consent. Shall I request consent to access your medical records?'"
            )

        # 3. Format the prompt
        doc_dir = self._get_doctor_directory_string()
        current_time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        base_prompt = get_prompt("scheduling_system").format(
            doctor_directory=doc_dir,
            patient_history=patient_history,
            current_time=current_time_str
        )
        return base_prompt + consent_instruction
