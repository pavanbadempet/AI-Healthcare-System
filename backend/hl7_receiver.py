"""HL7 v2 Ingestion Receiver & Parser for ClinOS Interoperability.

Parses standard HL7 v2 messages (ADT^A08 for Patient Update and ORU^R01 for Observation Result)
and synchronizes the parsed clinical data into the local database models.
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from backend.models.auth import User
from backend.models.clinical import VitalObservation

logger = logging.getLogger(__name__)

def parse_hl7_datetime(dt_str: str) -> datetime:
    """Parses HL7 datetime formats (e.g. YYYYMMDDHHMMSS or YYYYMMDD)."""
    if not dt_str:
        return datetime.now(timezone.utc)
    clean_str = dt_str.strip()
    try:
        if len(clean_str) >= 14:
            return datetime.strptime(clean_str[:14], "%Y%m%d%H%M%S").replace(tzinfo=timezone.utc)
        elif len(clean_str) >= 8:
            return datetime.strptime(clean_str[:8], "%Y%m%d").replace(tzinfo=timezone.utc)
    except ValueError:
        pass
    return datetime.now(timezone.utc)

def process_hl7_message(hl7_str: str, db: Session) -> Dict[str, Any]:
    """
    Parses a raw HL7 v2 message string, maps segments, and upserts clinical database records.
    Supports ADT^A08 (Patient profile updates) and ORU^R01 (Vital observations).
    """
    if not hl7_str:
        raise ValueError("Empty HL7 message payload")

    # Split message into segments supporting different carriage return / newline conventions
    raw_lines = [line.strip() for line in hl7_str.replace("\r\n", "\n").replace("\r", "\n").split("\n")]
    segments = [line for line in raw_lines if line]

    msh_fields: List[str] = []
    pid_fields: List[str] = []
    obx_segments: List[List[str]] = []

    for seg in segments:
        fields = seg.split("|")
        seg_type = fields[0]

        if seg_type == "MSH":
            msh_fields = fields
        elif seg_type == "PID":
            pid_fields = fields
        elif seg_type == "PV1":
            _pv1_fields = fields
        elif seg_type == "OBX":
            obx_segments.append(fields)

    if not msh_fields:
        raise ValueError("MSH segment is missing")

    # MSH field indices: MSH-9 (Message Type) is at index 8 in split('|')
    # Because fields[0] is 'MSH' and fields[1] is the separator itself, so index 8 corresponds to MSH-9.
    message_type = ""
    if len(msh_fields) > 8:
        message_type = msh_fields[8]

    if not message_type:
        raise ValueError("HL7 Message Type (MSH-9) is missing")

    # Normalize message type (e.g. ADT^A08 or ORU^R01)
    message_type = message_type.replace(" ", "")

    if not pid_fields:
        raise ValueError("PID segment is missing")

    # PID-3 (Patient Identifier) is at index 3
    patient_identifier = ""
    if len(pid_fields) > 3:
        patient_identifier = pid_fields[3].split("^")[0].strip()

    if not patient_identifier:
        raise ValueError("Patient Identifier (PID-3) is missing")

    # Fetch or create the Patient (represented by User model with role 'patient')
    try:
        patient_id = int(patient_identifier)
        patient = db.query(User).filter(User.id == patient_id, User.role == "patient").first()
    except ValueError:
        patient = db.query(User).filter(User.username == f"hl7_{patient_identifier}", User.role == "patient").first()

    if not patient:
        # Create a new patient stub
        patient = User(
            username=f"hl7_{patient_identifier}",
            hashed_password="placeholder_password",  # HL7 updates don't carry passwords
            role="patient"
        )
        db.add(patient)
        db.flush()  # Generate auto-increment ID if needed

    # Parse patient details from PID-5 (Name), PID-7 (DOB), PID-8 (Gender), PID-13 (Email/Contact)
    if len(pid_fields) > 5 and pid_fields[5]:
        name_parts = pid_fields[5].split("^")
        family_name = name_parts[0].strip()
        given_name = name_parts[1].strip() if len(name_parts) > 1 else ""
        patient.full_name = f"{given_name} {family_name}".strip()

    if len(pid_fields) > 7 and pid_fields[7]:
        dob_str = pid_fields[7].strip()
        if len(dob_str) >= 8:
            # Format DOB YYYY-MM-DD
            try:
                patient.dob = f"{dob_str[:4]}-{dob_str[4:6]}-{dob_str[6:8]}"
            except Exception:
                pass

    if len(pid_fields) > 8 and pid_fields[8]:
        gender_code = pid_fields[8].strip().upper()
        if gender_code == "F":
            patient.gender = "female"
        elif gender_code == "M":
            patient.gender = "male"
        else:
            patient.gender = "other"

    if len(pid_fields) > 13 and pid_fields[13]:
        # Simple extraction of email or phone
        patient.email = pid_fields[13].strip()

    db.flush()

    response_summary = {
        "status": "success",
        "message_type": message_type,
        "patient_id": patient.id,
        "patient_name": patient.full_name,
        "records_created": 0,
        "details": []
    }

    # Handle Patient Update ADT^A08
    if "ADT" in message_type:
        db.commit()
        response_summary["details"].append("Updated patient demographic data via ADT message.")
        return response_summary

    # Handle Observation Result ORU^R01
    elif "ORU" in message_type:
        vitals_dict: Dict[str, float] = {}
        observed_time: Optional[datetime] = None

        # Standard LOINC vital sign mappings
        # 8867-4: heart_rate, 8480-6: systolic_bp, 8462-4: diastolic_bp, 59408-5: spo2,
        # 8310-5: temperature_c, 9279-1: respiratory_rate, 2339-0: blood_glucose.
        loinc_map = {
            "8867-4": "heart_rate",
            "8480-6": "systolic_bp",
            "8462-4": "diastolic_bp",
            "59408-5": "spo2",
            "8310-5": "temperature_c",
            "9279-1": "respiratory_rate",
            "2339-0": "blood_glucose"
        }

        for obx in obx_segments:
            if len(obx) < 6:
                continue

            # OBX-3 (Observation Identifier) contains code^display^system
            obs_id = obx[3].split("^")[0].strip()
            # OBX-5 (Observation Value)
            val_str = obx[5].strip()

            # OBX-14 (Date/Time of Observation)
            if len(obx) > 14 and obx[14]:
                observed_time = parse_hl7_datetime(obx[14])

            if obs_id in loinc_map:
                try:
                    vitals_dict[loinc_map[obs_id]] = float(val_str)
                except ValueError:
                    logger.warning("Failed to parse numeric value '%s' for LOINC code %s", val_str, obs_id)

        if vitals_dict:
            # Create a VitalObservation record in the DB
            obs = VitalObservation(
                patient_id=patient.id,
                observed_at=observed_time or datetime.now(timezone.utc),
                source="device",
                **vitals_dict
            )
            db.add(obs)
            db.flush()
            response_summary["records_created"] = 1
            response_summary["details"].append(f"Ingested observation record containing vitals: {list(vitals_dict.keys())}.")

        db.commit()
        return response_summary

    else:
        raise NotImplementedError(f"Unsupported HL7 message type: {message_type}")
