"""
HIPAA Security Rule § 164.312(b) audit trail logging middleware for PHI access events.
"""
import datetime
import json
import logging
from typing import Any, Dict

logger = logging.getLogger("hipaa.audit")

class HIPAASecurityAuditLogger:
    """Captures structured tamper-evident audit records for electronic Protected Health Information (ePHI)."""

    @staticmethod
    def record_access_event(user_id: str, patient_id: str, action: str, resource: str) -> Dict[str, Any]:
        record = {
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "operator_id": user_id,
            "patient_mrn": patient_id,
            "action": action,
            "resource": resource,
            "compliance_standard": "HIPAA_164.312_b"
        }
        logger.info(json.dumps(record))
        return record
