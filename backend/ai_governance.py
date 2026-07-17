"""AI Governance and Regulatory Compliance Registry.

Catalogs clinical AI models, versions, intended uses, and FDA/EU AI Act postures.
Audits clinician override logs and tracks doctor-agreement rates for post-market surveillance.
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List
from sqlalchemy.orm import Session
from sqlalchemy import func

from backend.models.intelligence import ClinicalAICorrection
from backend import models

logger = logging.getLogger(__name__)

from dataclasses import dataclass

@dataclass
class AIFunctionRecord:
    name: str
    version: str
    intended_use: str
    clinical_claim: str
    audience: str
    regulatory_posture: str  # FDA CDS, EU AI Act High-Risk, Administrative etc.

# SOTA Registry of all active clinical AI components in ClinOS
REGISTRY: Dict[str, AIFunctionRecord] = {
    "heart_risk_prediction": AIFunctionRecord(
        name="heart_risk_prediction",
        version="2.4.1",
        intended_use="Cardiovascular disease risk screen for adult outpatients.",
        clinical_claim="Supports cardiovascular diagnosis based on vitals and demographics.",
        audience="Clinician review required",
        regulatory_posture="FDA Clinical Decision Support (CDS) Software Category 2",
    ),
    "diabetes_risk_prediction": AIFunctionRecord(
        name="diabetes_risk_prediction",
        version="1.8.2",
        intended_use="Type 2 diabetes risk screening.",
        clinical_claim="Predicts likelihood of hyperglycemia and insulin resistance.",
        audience="Clinician review required",
        regulatory_posture="FDA Clinical Decision Support (CDS) Software Category 2",
    ),
    "clinical_billing_audit": AIFunctionRecord(
        name="clinical_billing_audit",
        version="1.1.0",
        intended_use="Automated audit of SOAP notes for ICD-10 and CPT coding compliance.",
        clinical_claim="No clinical claims. Identifies potential coding errors and modifiers.",
        audience="Administrative staff / Billing auditors",
        regulatory_posture="Administrative / Non-Device",
    ),
    "ambient_scribe_soap": AIFunctionRecord(
        name="ambient_scribe_soap",
        version="3.0.1",
        intended_use="Speech-to-text consultation SOAP note generation.",
        clinical_claim="Speeds up clinical documentation. Does not diagnose or recommend treatment.",
        audience="Licensed Clinician review and signature required",
        regulatory_posture="Administrative / Non-Device",
    ),
    "emergency_call_routing": AIFunctionRecord(
        name="emergency_call_routing",
        version="1.0.5",
        intended_use="Telemetry warning emergency call script generation.",
        clinical_claim="Triggers urgent outreach for cardiac alarms. Direct clinician on-call review.",
        regulatory_posture="EU AI Act High-Risk Class IIa",
        audience="Licensed Cardiologist / Emergency response team",
    ),
}

def get_registered_functions() -> List[Dict[str, Any]]:
    """Returns a list of all registered clinical AI systems and their postures."""
    return [
        {
            "name": rec.name,
            "version": rec.version,
            "intended_use": rec.intended_use,
            "clinical_claim": rec.clinical_claim,
            "audience": rec.audience,
            "regulatory_posture": rec.regulatory_posture,
        }
        for rec in REGISTRY.values()
    ]

def log_clinician_override(
    db: Session,
    patient_id: int,
    clinician_id: int,
    function_name: str,
    original_ai_output: str,
    corrected_output: Optional[str],
    override_action: str,  # accepted | overridden | ignored
    override_reason: Optional[str] = None,
) -> ClinicalAICorrection:
    """Log an AI decision audit event representing clinician review, validation, or override."""
    if function_name not in REGISTRY:
        logger.warning("Logging override for unregistered AI function: %s", function_name)

    correction = ClinicalAICorrection(
        patient_id=patient_id,
        clinician_id=clinician_id,
        function_name=function_name,
        original_ai_output=original_ai_output,
        corrected_output=corrected_output,
        override_action=override_action.strip().lower(),
        override_reason=override_reason,
        created_at=datetime.now(timezone.utc)
    )
    db.add(correction)
    db.commit()
    db.refresh(correction)
    logger.info("Recorded AI override event for %s. Action: %s", function_name, override_action)
    return correction

def get_governance_report(db: Session) -> List[Dict[str, Any]]:
    """Computes clinical agreement rates and drift telemetry for post-market monitoring."""
    report = []
    
    # Query override stats grouped by function
    stats = db.query(
        ClinicalAICorrection.function_name,
        ClinicalAICorrection.override_action,
        func.count(ClinicalAICorrection.id)
    ).group_by(
        ClinicalAICorrection.function_name,
        ClinicalAICorrection.override_action
    ).all()

    # Structure data by function
    matrix: Dict[str, Dict[str, int]] = {}
    for func_name, action, cnt in stats:
        if func_name not in matrix:
            matrix[func_name] = {"accepted": 0, "overridden": 0, "ignored": 0}
        if action in matrix[func_name]:
            matrix[func_name][action] = cnt

    for func_name, rec in REGISTRY.items():
        counts = matrix.get(func_name, {"accepted": 0, "overridden": 0, "ignored": 0})
        total = sum(counts.values())
        agreement_rate = (counts["accepted"] / total) if total > 0 else 1.0

        report.append({
            "function_name": func_name,
            "version": rec.version,
            "regulatory_posture": rec.regulatory_posture,
            "total_reviews": total,
            "accepted_count": counts["accepted"],
            "overridden_count": counts["overridden"],
            "ignored_count": counts["ignored"],
            "agreement_rate": round(agreement_rate, 3),
            "status": "stable" if agreement_rate >= 0.85 else "needs_calibration"
        })

    return report
