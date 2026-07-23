"""
Patient Triage Clinical Referral Router Agent
==============================================
Routes patient referrals to appropriate sub-specialty clinics (Cardiology, Nephrology,
Neurology, Oncology) based on diagnosis codes, acuity, and clinic waitlist priorities.
"""

from typing import Dict, List, Optional

SPECIALTY_CLINIC_MAP = {
    "cardiology": ["I10", "I25.10", "I50.9", "chest pain", "heart failure"],
    "nephrology": ["N18.3", "N18.4", "N18.5", "egfr", "ckd", "kidney"],
    "neurology": ["G43.9", "G40.9", "stroke", "seizure", "migraine"],
    "oncology": ["C50.9", "C34.9", "carcinoma", "neoplasm", "tumor"],
}


class ClinicalReferralRouterAgent:
    """Routes patient cases to appropriate sub-specialty clinics."""

    def route_referral(
        self,
        patient_id: int,
        primary_complaint: str,
        icd10_codes: Optional[List[str]] = None,
        urgency_level: str = "ROUTINE",  # 'STAT', 'URGENT', 'ROUTINE'
    ) -> Dict[str, any]:
        text_lower = primary_complaint.lower()
        patient_icd10 = set(icd10_codes or [])
        matched_specialty = "GENERAL_INTERNAL_MEDICINE"

        for specialty, keywords in SPECIALTY_CLINIC_MAP.items():
            if any(kw in text_lower for kw in keywords) or any(code in patient_icd10 for code in keywords):
                matched_specialty = specialty.upper()
                break

        target_days = 1 if urgency_level == "STAT" else (7 if urgency_level == "URGENT" else 30)

        return {
            "patient_id": patient_id,
            "target_specialty": matched_specialty,
            "urgency_level": urgency_level,
            "max_wait_days": target_days,
            "routing_status": "REFERRAL_ROUTED",
            "clinical_notes": f"Referral routed to {matched_specialty} with target consultation within {target_days} days.",
        }


# Singleton agent instance
referral_router_agent = ClinicalReferralRouterAgent()
