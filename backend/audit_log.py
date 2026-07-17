"""HIPAA-Compliant Patient Data Access Auditing.

Generates FHIR-compliant AuditEvent records for all patient profile reads,
mutations, and clinical queries to meet security compliance standards.
"""

import logging
import threading
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Thread-safe in-memory audit logs list for unit test validation
_audit_logs_lock = threading.Lock()
_audit_logs: List[Dict[str, Any]] = []

def clear_audit_logs() -> None:
    """Clears all logged audit events (useful for unit tests)."""
    with _audit_logs_lock:
        _audit_logs.clear()

def get_logged_audit_events() -> List[Dict[str, Any]]:
    """Returns a list of all logged FHIR AuditEvent dictionaries."""
    with _audit_logs_lock:
        return list(_audit_logs)

def log_clinical_access_event(
    action: str,          # "C" (Create), "R" (Read), "U" (Update), "D" (Delete)
    actor_id: str,       # ID/username of doctor, patient, or system agent
    patient_id: int,     # Patient database key ID
    outcome_code: str = "0",  # "0" for Success, "4" for Minor Failure, "8" for Serious Failure
    description: Optional[str] = None
) -> Dict[str, Any]:
    """
    Creates and records a standard FHIR-compliant AuditEvent.
    Adheres strictly to HIPAA requirements: logs actions, actors, targets, outcomes, and timestamps
    without exposing sensitive health PII in the logs.
    """
    # Map outcome code description
    outcome_desc = {
        "0": "Success",
        "4": "Minor Failure",
        "8": "Serious Failure",
        "12": "Major Failure"
    }.get(outcome_code, "unknown")

    # Construct standard FHIR AuditEvent
    audit_event = {
        "resourceType": "AuditEvent",
        "type": {
            "system": "http://dicom.nema.org/resources/ontology/DCM",
            "code": "110110",
            "display": "Patient Record"
        },
        "action": action,
        "recorded": datetime.now(timezone.utc).isoformat(),
        "outcome": outcome_code,
        "outcomeDesc": outcome_desc,
        "agent": [
            {
                "requestor": True,
                "userId": {
                    "value": actor_id
                }
            }
        ],
        "entity": [
            {
                "what": {
                    "reference": f"Patient/{patient_id}"
                },
                "type": {
                    "system": "http://terminology.hl7.org/CodeSystem/audit-entity-type",
                    "code": "2",
                    "display": "System Object"
                }
            }
        ]
    }

    if description:
        audit_event["type"]["display"] += f" - {description}"

    with _audit_logs_lock:
        _audit_logs.append(audit_event)

    # Output to standard logger securely (safe from exposing PII, logs only reference IDs)
    logger.info(
        "HIPAA Access Audit: Action=%s, Actor=%s, PatientReference=Patient/%d, Outcome=%s",
        action, actor_id, patient_id, outcome_desc
    )

    return audit_event
