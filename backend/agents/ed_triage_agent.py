"""
Emergency Department (ED) Triage & ESI Calculator Agent
======================================================
Calculates Emergency Severity Index (ESI Level 1-5) based on patient acuity,
vital sign stability, high-risk flags, and projected resource needs.
"""

from typing import Dict


class EmergencyTriageAgent:
    """Calculates ESI Triage levels for Emergency Department intake."""

    def evaluate_esi_triage(
        self,
        chief_complaint: str,
        heart_rate: float,
        systolic_bp: float,
        oxygen_sat: float,
        respiratory_rate: float,
        is_unresponsive_or_dying: bool = False,
        is_high_risk_situation: bool = False,
        projected_resources_needed: int = 1,
    ) -> Dict[str, any]:
        # ESI Level 1: Immediate life-saving intervention required
        if is_unresponsive_or_dying or heart_rate > 150 or systolic_bp < 80 or oxygen_sat < 85:
            return {
                "esi_level": 1,
                "acuity_category": "IMMEDIATE_RESUSCITATION",
                "target_time_to_physician_min": 0,
                "clinical_description": "Immediate life-saving intervention required (Resuscitation Area).",
                "recommended_area": "Trauma / Resuscitation Bay",
            }

        # ESI Level 2: High risk situation / confused / severe pain
        if is_high_risk_situation or oxygen_sat < 92 or systolic_bp > 200 or heart_rate > 130:
            return {
                "esi_level": 2,
                "acuity_category": "EMERGENT",
                "target_time_to_physician_min": 10,
                "clinical_description": "High-risk situation or severe vital sign abnormality (Emergent).",
                "recommended_area": "Acute ED Care Bed",
            }

        # ESI Level 3, 4, 5 based on projected resource needs (labs, ECG, X-ray, IV meds)
        if projected_resources_needed >= 2:
            return {
                "esi_level": 3,
                "acuity_category": "URGENT",
                "target_time_to_physician_min": 30,
                "clinical_description": "Urgent presentation requiring multiple resources (labs, imaging, IV meds).",
                "recommended_area": "Main ED Treatment Area",
            }
        elif projected_resources_needed == 1:
            return {
                "esi_level": 4,
                "acuity_category": "LESS_URGENT",
                "target_time_to_physician_min": 60,
                "clinical_description": "Less urgent presentation requiring 1 resource (single X-ray or lab).",
                "recommended_area": "Fast Track / Express Care",
            }
        else:
            return {
                "esi_level": 5,
                "acuity_category": "NON_URGENT",
                "target_time_to_physician_min": 120,
                "clinical_description": "Non-urgent presentation requiring zero complex ED resources.",
                "recommended_area": "Outpatient Clinic / Fast Track",
            }


# Singleton triage agent instance
ed_triage_agent = EmergencyTriageAgent()
