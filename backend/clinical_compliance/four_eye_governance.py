"""
Four-Eye Check Clinical Governance Engine
Enforces dual-clinician sign-off, multi-party attestation, and cryptographic verification
for high-risk medical procedures, critical AI predictions, and controlled substance orders.
"""

from __future__ import annotations

import enum
import hashlib
import hmac
import logging
import os
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

SECRET_KEY = os.getenv("FOUR_EYE_SECRET_KEY", "clinical-four-eye-hmac-root-secret-2026")


class FourEyeActionType(str, enum.Enum):
    HIGH_RISK_PRESCRIPTION = "HIGH_RISK_PRESCRIPTION"
    CRITICAL_AI_DIAGNOSIS = "CRITICAL_AI_DIAGNOSIS"
    SURGICAL_OR_ADMISSION_ORDER = "SURGICAL_OR_ADMISSION_ORDER"
    PATIENT_RECORD_DELETION = "PATIENT_RECORD_DELETION"
    MODEL_RETRAINING_RELEASE = "MODEL_RETRAINING_RELEASE"
    INVASIVE_PROCEDURE_ORDER = "INVASIVE_PROCEDURE_ORDER"


class FourEyeStatus(str, enum.Enum):
    PENDING_PEER_REVIEW = "PENDING_PEER_REVIEW"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"
    CMO_OVERRIDDEN = "CMO_OVERRIDDEN"


class FourEyeCheckRequest(BaseModel):
    request_id: str
    action_type: FourEyeActionType
    patient_id: int
    initiator_doctor_id: int
    initiator_doctor_name: str
    initiator_npi: str
    clinical_justification: str
    payload: Dict[str, Any]
    created_at: str
    status: FourEyeStatus = FourEyeStatus.PENDING_PEER_REVIEW
    reviewer_doctor_id: Optional[int] = None
    reviewer_doctor_name: Optional[str] = None
    reviewer_npi: Optional[str] = None
    reviewer_comments: Optional[str] = None
    reviewed_at: Optional[str] = None
    cryptographic_hmac: str = ""


class FourEyeGovernanceEngine:
    """
    Enterprise-grade Four-Eye Check Governance Engine.
    Guarantees that no single clinician can execute life-critical, irreversible,
    or high-risk AI decisions without secondary peer clinician verification.
    """

    def __init__(self):
        self._requests: Dict[str, FourEyeCheckRequest] = {}

    def _generate_hmac(self, request_id: str, action: str, patient_id: int, doc_a: int, doc_b: Optional[int]) -> str:
        """Generates an immutable cryptographic HMAC signature binding both clinicians to the action."""
        msg = f"{request_id}:{action}:{patient_id}:{doc_a}:{doc_b or 0}"
        return hmac.new(SECRET_KEY.encode("utf-8"), msg.encode("utf-8"), hashlib.sha256).hexdigest()

    def submit_action_for_review(
        self,
        action_type: FourEyeActionType,
        patient_id: int,
        initiator_id: int,
        initiator_name: str,
        initiator_npi: str,
        clinical_justification: str,
        payload: Dict[str, Any]
    ) -> FourEyeCheckRequest:
        """Submits a high-risk clinical action to the Four-Eye Governance queue."""
        import uuid
        request_id = f"4EYE-{uuid.uuid4().hex[:10].upper()}"
        now_str = datetime.now(timezone.utc).isoformat()

        req = FourEyeCheckRequest(
            request_id=request_id,
            action_type=action_type,
            patient_id=patient_id,
            initiator_doctor_id=initiator_id,
            initiator_doctor_name=initiator_name,
            initiator_npi=initiator_npi,
            clinical_justification=clinical_justification,
            payload=payload,
            created_at=now_str,
            status=FourEyeStatus.PENDING_PEER_REVIEW,
            cryptographic_hmac=self._generate_hmac(request_id, action_type.value, patient_id, initiator_id, None)
        )

        self._requests[request_id] = req
        logger.info(
            "Submitted Four-Eye Check request %s for action %s",
            request_id, action_type.value
        )
        return req

    def peer_signoff(
        self,
        request_id: str,
        reviewer_id: int,
        reviewer_name: str,
        reviewer_npi: str,
        approved: bool,
        comments: str
    ) -> FourEyeCheckRequest:
        """
        Executes secondary clinician review.
        Enforces rule: reviewer_id != initiator_doctor_id (Strict Anti-Self-Approval Gate).
        """
        if request_id not in self._requests:
            raise ValueError(f"Four-Eye Check request {request_id} not found.")

        req = self._requests[request_id]

        if req.status != FourEyeStatus.PENDING_PEER_REVIEW:
            raise ValueError(f"Request {request_id} is already in state: {req.status.value}")

        # Strict Anti-Self-Approval Rule
        if reviewer_id == req.initiator_doctor_id:
            logger.warning(
                "Rejected self-approval attempt on Four-Eye Check %s",
                request_id
            )
            raise PermissionError("Four-Eye Policy Violation: Initiating clinician cannot peer-approve their own request.")

        now_str = datetime.now(timezone.utc).isoformat()
        req.reviewer_doctor_id = reviewer_id
        req.reviewer_doctor_name = reviewer_name
        req.reviewer_npi = reviewer_npi
        req.reviewer_comments = comments
        req.reviewed_at = now_str
        req.status = FourEyeStatus.APPROVED if approved else FourEyeStatus.REJECTED
        req.cryptographic_hmac = self._generate_hmac(
            request_id, req.action_type.value, req.patient_id, req.initiator_doctor_id, reviewer_id
        )

        logger.info(
            "Four-Eye Check request %s reviewed -> Status: %s",
            request_id, req.status.value
        )
        return req

    def get_pending_requests(self, exclude_doctor_id: Optional[int] = None) -> List[FourEyeCheckRequest]:
        """Returns all pending requests that the querying clinician is eligible to review."""
        pending = [r for r in self._requests.values() if r.status == FourEyeStatus.PENDING_PEER_REVIEW]
        if exclude_doctor_id is not None:
            pending = [r for r in pending if r.initiator_doctor_id != exclude_doctor_id]
        return sorted(pending, key=lambda x: x.created_at, reverse=True)

    def get_request(self, request_id: str) -> Optional[FourEyeCheckRequest]:
        """Retrieves a specific governance record."""
        return self._requests.get(request_id)

    def is_action_authorized(self, request_id: str) -> bool:
        """Verifies if a Four-Eye action is cryptographically approved and authorized for execution."""
        req = self._requests.get(request_id)
        if not req or req.status != FourEyeStatus.APPROVED:
            return False

        # Verify HMAC signature integrity
        expected_hmac = self._generate_hmac(
            request_id, req.action_type.value, req.patient_id, req.initiator_doctor_id, req.reviewer_doctor_id
        )
        return hmac.compare_digest(req.cryptographic_hmac, expected_hmac)


# Global Singleton
four_eye_engine = FourEyeGovernanceEngine()
