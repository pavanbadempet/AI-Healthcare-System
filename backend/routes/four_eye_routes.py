"""
Four-Eye Governance and Multi-Level AI Safety API Router
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from .. import auth, models
from ..ai_governance_guardian import (
    GovernanceCheckResult,
    ai_guardian,
)
from ..clinical_compliance.four_eye_governance import (
    FourEyeActionType,
    FourEyeCheckRequest,
    four_eye_engine,
)

router = APIRouter(prefix="/v1/governance", tags=["Four-Eye Clinical Governance & AI Safety"])


class FourEyeSubmitPayload(BaseModel):
    action_type: FourEyeActionType
    patient_id: int
    clinical_justification: str
    payload: Dict[str, Any]


class FourEyeReviewPayload(BaseModel):
    request_id: str
    approved: bool
    comments: str
    reviewer_npi: Optional[str] = "1928401928"


class AIEvaluationPayload(BaseModel):
    prompt_or_advice: str
    patient_id: Optional[int] = 1
    predicted_probability: Optional[float] = 0.5
    confidence_interval_width: Optional[float] = 0.15
    allergies: Optional[List[str]] = Field(default_factory=list)
    medication_name: Optional[str] = None


@router.get("/four-eye/pending", response_model=List[FourEyeCheckRequest])
def list_pending_four_eye_reviews(
    current_user: models.User = Depends(auth.get_current_user)
) -> List[FourEyeCheckRequest]:
    """
    Returns all pending clinical actions awaiting peer sign-off.
    Automatically excludes requests initiated by the calling doctor (Anti-Self-Approval Gate).
    """
    return four_eye_engine.get_pending_requests(exclude_doctor_id=current_user.id)


@router.post("/four-eye/submit", response_model=FourEyeCheckRequest, status_code=status.HTTP_201_CREATED)
def submit_for_four_eye_review(
    body: FourEyeSubmitPayload,
    current_user: models.User = Depends(auth.get_current_user)
) -> FourEyeCheckRequest:
    """Submits a critical or high-risk clinical action for secondary physician verification."""
    doctor_npi = getattr(current_user, "npi", "1928401928") or "1928401928"
    doctor_name = current_user.full_name or current_user.username or "Attending Physician"

    req = four_eye_engine.submit_action_for_review(
        action_type=body.action_type,
        patient_id=body.patient_id,
        initiator_id=current_user.id,
        initiator_name=doctor_name,
        initiator_npi=doctor_npi,
        clinical_justification=body.clinical_justification,
        payload=body.payload
    )
    return req


@router.post("/four-eye/review", response_model=FourEyeCheckRequest)
def peer_review_action(
    body: FourEyeReviewPayload,
    current_user: models.User = Depends(auth.get_current_user)
) -> FourEyeCheckRequest:
    """
    Secondary clinician signs off on a pending high-risk action.
    Strictly forbids self-approval (Doctor B != Doctor A).
    """
    doctor_npi = body.reviewer_npi or getattr(current_user, "npi", "1928401928") or "1928401928"
    doctor_name = current_user.full_name or current_user.username or "Reviewing Physician"

    try:
        updated_req = four_eye_engine.peer_signoff(
            request_id=body.request_id,
            reviewer_id=current_user.id,
            reviewer_name=doctor_name,
            reviewer_npi=doctor_npi,
            approved=body.approved,
            comments=body.comments
        )
        return updated_req
    except PermissionError as pe:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(pe))
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(ve))


@router.get("/four-eye/verify/{request_id}")
def verify_four_eye_signature(
    request_id: str,
    current_user: models.User = Depends(auth.get_current_user)
) -> Dict[str, Any]:
    """Cryptographically verifies the dual-clinician SHA-256 HMAC signature proof."""
    req = four_eye_engine.get_request(request_id)
    if not req:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found")

    is_valid = four_eye_engine.is_action_authorized(request_id)
    return {
        "request_id": request_id,
        "action_type": req.action_type.value,
        "status": req.status.value,
        "cryptographic_hmac_valid": is_valid,
        "initiator_doctor": req.initiator_doctor_name,
        "reviewer_doctor": req.reviewer_doctor_name,
        "reviewed_at": req.reviewed_at
    }


@router.post("/ai-guardian/evaluate", response_model=GovernanceCheckResult)
def evaluate_ai_safety_pipeline(
    body: AIEvaluationPayload,
    current_user: models.User = Depends(auth.get_current_user)
) -> GovernanceCheckResult:
    """
    Executes the 4-Level AI Governance Guardian on clinical advice, model output, or order payloads.
    """
    doctor_npi = getattr(current_user, "npi", "1928401928") or "1928401928"
    doctor_name = current_user.full_name or current_user.username or "Attending Physician"

    payload_data = {
        "advice": body.prompt_or_advice,
        "probability": body.predicted_probability or 0.5,
        "confidence_interval_width": body.confidence_interval_width or 0.15,
        "allergies": body.allergies or [],
        "medication_name": body.medication_name or ""
    }

    result = ai_guardian.evaluate_level_4_action_routing(
        action_type=FourEyeActionType.CRITICAL_AI_DIAGNOSIS,
        patient_id=body.patient_id or 1,
        initiator_id=current_user.id,
        initiator_name=doctor_name,
        initiator_npi=doctor_npi,
        payload=payload_data
    )
    return result
