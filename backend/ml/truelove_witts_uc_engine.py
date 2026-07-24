"""
Ulcerative Colitis Truelove & Witts Severity Index Engine
==========================================================
Classifies acute ulcerative colitis flares (Mild, Moderate, Severe/Fulminant)
based on bloody bowel movements, fever, tachycardia, anemia, and ESR.
"""

from typing import Dict


class TrueloveWittsUcEngine:
    """Classifies acute Ulcerative Colitis disease severity via Truelove & Witts criteria."""

    def classify_uc_severity(
        self,
        bloody_stools_per_day: int,
        pulse_rate_bpm: int = 75,
        temperature_celsius: float = 36.8,
        hemoglobin_g_dL: float = 13.5,
        esr_mm_hr: float = 15.0,
    ) -> Dict[str, any]:
        systemic_toxicity = (
            pulse_rate_bpm > 90
            or temperature_celsius > 37.5
            or hemoglobin_g_dL < 10.5
            or esr_mm_hr > 30.0
        )

        severity = "MILD_ULCERATIVE_COLITIS"
        hospitalization = False

        if bloody_stools_per_day >= 6 and systemic_toxicity:
            severity = "SEVERE_FULMINANT_ULCERATIVE_COLITIS"
            hospitalization = True
        elif bloody_stools_per_day >= 4 or systemic_toxicity:
            severity = "MODERATE_ULCERATIVE_COLITIS"

        recommendation = "Outpatient oral 5-ASA (Mesalamine 4.8g/day) + topical Mesalamine enema"
        if hospitalization:
            recommendation = "Stat Hospital Admission, IV Hydrocortisone 100mg Q6H, flexible sigmoidoscopy, & evaluate Infliximab / Cyclosporine rescue therapy at Day 3"
        elif severity == "MODERATE_ULCERATIVE_COLITIS":
            recommendation = "Add oral Prednisolone 40mg/day with 8-week taper & 5-ASA optimization"

        return {
            "bloody_stools_per_day": bloody_stools_per_day,
            "systemic_toxicity_present": systemic_toxicity,
            "uc_severity_grade": severity,
            "inpatient_iv_steroid_rescue_indicated": hospitalization,
            "clinical_recommendation": recommendation,
            "status": "CLASSIFICATION_COMPLETE",
        }


# Singleton engine instance
truelove_witts_engine = TrueloveWittsUcEngine()
