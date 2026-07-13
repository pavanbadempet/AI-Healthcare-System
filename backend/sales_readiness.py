"""Admin sales-readiness matrix for regulated market rollout."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from fastapi import APIRouter, Depends

from . import admin as admin_dependencies
from . import models

router = APIRouter(prefix="/admin", tags=["Sales Readiness"])


SALES_READINESS: dict[str, Any] = {
    "product_positioning": {
        "primary_market": "India",
        "safe_category": "AI-assisted clinic workflow software",
        "clinical_posture": "clinician-in-the-loop",
        "target_buyers": [
            "small clinics",
            "specialist clinics",
            "clinic groups with 2-10 locations",
            "telemedicine practices with registered clinicians",
        ],
        "primary_value": [
            "appointment workflow",
            "patient record organization",
            "clinician-reviewed AI summaries",
            "screening-result documentation",
            "patient communication support",
        ],
    },
    "blocked_claims": [
        "autonomous diagnosis",
        "autonomous triage",
        "independent prescribing",
        "replaces clinicians",
        "guaranteed diagnosis",
        "regulator-cleared medical device",
        "hospital-enterprise compliance already completed",
    ],
    "required_artifacts": [
        "trust baseline",
        "India privacy notice",
        "clinic data processing terms",
        "pilot order form",
        "security questionnaire answers",
        "subprocessor and hosting-region list",
        "incident response contact process",
        "data retention and deletion process",
        "production deployment checklist",
    ],
    "markets": [
        {
            "code": "IN",
            "name": "India",
            "priority": 1,
            "status": "ready_for_controlled_clinic_pilots",
            "sales_motion": "Founder-led sales to small clinics and specialist practices.",
            "ready_controls": [
                "role-based access control",
                "PHI-safe audit logging",
                "admin audit review",
                "clinician-in-the-loop AI posture",
                "patient-scoped health records",
                "production secret requirement",
            ],
            "paid_pilot_requirements": [
                "DPDP Act privacy notice",
                "clinic data processing terms",
                "ABDM compatibility roadmap",
                "telemedicine clinician accountability language",
                "incident response contact",
                "pilot success metrics",
            ],
            "expansion_requirements": [
                "ABDM sandbox integration plan",
                "local hosting decision",
                "formal legal review",
                "medical-device software review before diagnostic claims",
            ],
        },
        {
            "code": "EU",
            "name": "European Union",
            "priority": 2,
            "status": "expansion_requires_gdpr_ai_act_review",
            "sales_motion": "Controlled pilots only after privacy and AI-risk review.",
            "paid_pilot_requirements": [
                "GDPR privacy notice",
                "data processing agreement",
                "data subject rights workflow",
                "cross-border transfer review",
                "AI Act and medical-device intended-use review",
            ],
            "expansion_requirements": [
                "EU representative decision",
                "DPIA template",
                "clinical-risk classification",
                "post-market monitoring plan if regulated",
            ],
        },
        {
            "code": "US",
            "name": "United States",
            "priority": 3,
            "status": "expansion_requires_baa_and_hipaa_security_review",
            "sales_motion": "Small clinics after business-associate contract readiness.",
            "paid_pilot_requirements": [
                "business associate agreement readiness",
                "HIPAA Security Rule safeguards mapping",
                "breach notification process",
                "clinical decision support intended-use review",
                "state privacy law review",
            ],
            "expansion_requirements": [
                "security risk assessment",
                "pen test",
                "cyber insurance decision",
                "FDA review before diagnostic or treatment claims",
            ],
        },
        {
            "code": "OTHER",
            "name": "Other countries",
            "priority": 4,
            "status": "country_by_country_review_required",
            "sales_motion": "Enter only after local privacy, medical-software, and telemedicine rules are checked.",
            "paid_pilot_requirements": [
                "local health-data classification",
                "local clinician licensing rules",
                "data residency decision",
                "breach notification rules",
                "medical-software classification",
            ],
            "expansion_requirements": [
                "local counsel review",
                "localized privacy notice",
                "localized support and incident contacts",
            ],
        },
    ],
    "next_sales_actions": [
        "package India privacy notice and clinic data terms",
        "prepare a two-week pilot offer for 3-5 clinics",
        "define pilot metrics: appointments booked, report time saved, clinician review acceptance, support tickets",
        "create a demo dataset with synthetic patients only",
        "run a production deployment checklist before any real clinic data",
    ],
    "source_documents": [
        "docs/TRUST_BASELINE.md",
        "docs/SALES_READINESS_INDIA_FIRST.md",
        "docs/SECURITY_QUESTIONNAIRE.md",
        "docs/CLINIC_PILOT_PLAYBOOK.md",
        "docs/PRICING_AND_PACKAGING.md",
        "docs/CONTRACT_PACKET_CHECKLIST.md",
    ],
}


@router.get("/sales-readiness")
def get_sales_readiness(
    _admin: models.User = Depends(admin_dependencies.get_current_admin),
) -> dict[str, Any]:
    """Return the current clinic sales-readiness posture for admins."""
    return deepcopy(SALES_READINESS)
