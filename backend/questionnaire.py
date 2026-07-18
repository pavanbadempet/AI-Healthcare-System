"""FHIR Questionnaire Ingestion Engine for AI Healthcare System Interoperability.

Ingests standard FHIR QuestionnaireResponse resources, maps them against their
corresponding Questionnaire definitions, and saves structured observations to the database.
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict

from sqlalchemy.orm import Session

from backend.models.auth import User
from backend.models.clinical import VitalObservation

logger = logging.getLogger(__name__)

def ingest_fhir_questionnaire_response(
    response_json: Dict[str, Any],
    questionnaire_json: Dict[str, Any],
    db: Session
) -> Dict[str, Any]:
    """
    Ingests a FHIR QuestionnaireResponse, matches answers against the Questionnaire schema,
    resolves clinical codes (LOINC), and upserts a structured VitalObservation record.
    """
    if not response_json or not questionnaire_json:
        raise ValueError("Invalid payload: both response and questionnaire are required")

    # 1. Validate Resource Types
    if response_json.get("resourceType") != "QuestionnaireResponse":
        raise ValueError("Resource is not a FHIR QuestionnaireResponse")
    if questionnaire_json.get("resourceType") != "Questionnaire":
        raise ValueError("Resource is not a FHIR Questionnaire")

    # 2. Extract and Validate Patient
    subject_ref = response_json.get("subject", {}).get("reference", "")
    if not subject_ref or not subject_ref.startswith("Patient/"):
        raise ValueError("Missing or invalid subject reference in QuestionnaireResponse")

    patient_id_str = subject_ref.split("/")[-1].strip()
    try:
        patient_id = int(patient_id_str)
        patient = db.query(User).filter(User.id == patient_id, User.role == "patient").first()
    except ValueError:
        patient = db.query(User).filter(User.username == f"fhir_{patient_id_str}", User.role == "patient").first()

    if not patient:
        # Create a new patient stub if not exists
        patient = User(
            username=f"fhir_{patient_id_str}",
            hashed_password="placeholder_password",
            role="patient"
        )
        db.add(patient)
        db.flush()

    # 3. Build Questionnaire linkId -> LOINC Code Map
    link_id_to_loinc: Dict[str, str] = {}
    for item in questionnaire_json.get("item", []):
        link_id = item.get("linkId")
        if not link_id:
            continue
        codes = item.get("code", [])
        for code_entry in codes:
            # Look for LOINC coding system
            system = code_entry.get("system", "").lower()
            code_val = code_entry.get("code")
            if "loinc" in system and code_val:
                link_id_to_loinc[link_id] = code_val
                break

    # 4. Parse Answers from QuestionnaireResponse
    vitals_dict: Dict[str, float] = {}

    # LOINC code to VitalObservation attribute mapping
    loinc_map = {
        "8867-4": "heart_rate",
        "8480-6": "systolic_bp",
        "8462-4": "diastolic_bp",
        "59408-5": "spo2",
        "8310-5": "temperature_c",
        "9279-1": "respiratory_rate",
        "2339-0": "blood_glucose"
    }

    response_items = response_json.get("item", [])
    for resp_item in response_items:
        link_id = resp_item.get("linkId")
        answers = resp_item.get("answer", [])
        if not link_id or not answers:
            continue

        loinc_code = link_id_to_loinc.get(link_id)
        if not loinc_code or loinc_code not in loinc_map:
            continue

        attr_name = loinc_map[loinc_code]
        first_answer = answers[0]

        # Support various FHIR answer value types
        val = None
        for key in ["valueDecimal", "valueInteger", "valueQuantity", "valueString", "valueBoolean"]:
            if key in first_answer:
                if key == "valueQuantity":
                    val = first_answer[key].get("value")
                else:
                    val = first_answer[key]
                break

        if val is not None:
            try:
                vitals_dict[attr_name] = float(val)
            except (ValueError, TypeError):
                logger.warning("Could not convert answer value %s to float for linkId %s", val, link_id)

    # 5. Extract Timestamps
    authored_str = response_json.get("authored")
    observed_time = datetime.now(timezone.utc)
    if authored_str:
        try:
            # Handle ISO timestamp formats
            cleaned_time = authored_str.replace("Z", "+00:00")
            observed_time = datetime.fromisoformat(cleaned_time)
        except Exception:
            pass

    # 6. Save observations to database
    records_created = 0
    if vitals_dict:
        obs = VitalObservation(
            patient_id=patient.id,
            observed_at=observed_time,
            source="patient_reported",
            **vitals_dict
        )
        db.add(obs)
        db.flush()
        records_created = 1

    db.commit()

    return {
        "status": "success",
        "patient_id": patient.id,
        "questionnaire_id": questionnaire_json.get("id", "unknown"),
        "records_created": records_created,
        "vitals_mapped": list(vitals_dict.keys())
    }
