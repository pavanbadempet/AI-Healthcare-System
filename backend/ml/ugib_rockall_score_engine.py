"""
Acute Upper Gastrointestinal Bleeding (UGIB) Full Rockall Score Engine
========================================================================
Calculates Full Rockall Risk Score (Age, Shock status, Comorbidities, Endoscopic diagnosis, Stigmata of hemorrhage)
to predict rebleeding risk (0-50%) and 30-day mortality (0-40%).
"""

from typing import Dict


class UgibRockallScoreEngine:
    """Calculates Full Rockall Risk Score for post-endoscopy UGIB prognosis."""

    def calculate_full_rockall_score(
        self,
        age_years: int,
        pulse_bpm: float = 80.0,
        systolic_bp_mmHg: float = 120.0,
        major_comorbidities: str = "NONE",  # NONE, MAJOR_ORGAN_FAILURE, RENAL_FAILURE_LIVER_FAILURE_MALIGNANCY
        endoscopic_diagnosis: str = "MALLORY_WEISS_OR_NO_LESION",  # MALLORY_WEISS_OR_NO_LESION, ALL_OTHER_DIAGNOSES, GI_MALIGNANCY
        stigmata_of_hemorrhage: str = "CLEAN_BASE_OR_NO_STIGMATA",  # CLEAN_BASE_OR_NO_STIGMATA, BLOOD_CLOT_SPURTING_VESSEL
    ) -> Dict[str, any]:
        score = 0

        # Age
        if age_years >= 80:
            score += 2
        elif age_years >= 60:
            score += 1

        # Shock
        if systolic_bp_mmHg < 100.0:
            score += 2
        elif pulse_bpm >= 100.0:
            score += 1

        # Comorbidities
        if major_comorbidities == "RENAL_FAILURE_LIVER_FAILURE_MALIGNANCY":
            score += 3
        elif major_comorbidities == "MAJOR_ORGAN_FAILURE":
            score += 2

        # Endoscopic diagnosis
        if endoscopic_diagnosis == "GI_MALIGNANCY":
            score += 2
        elif endoscopic_diagnosis == "ALL_OTHER_DIAGNOSES":
            score += 1

        # Stigmata
        if stigmata_of_hemorrhage == "BLOOD_CLOT_SPURTING_VESSEL":
            score += 2

        risk_category = "LOW_RISK"
        rebleed_risk = "< 5%"
        mortality_risk = "< 1%"

        if score >= 8:
            risk_category = "VERY_HIGH_RISK"
            rebleed_risk = "> 40%"
            mortality_risk = "> 25%"
        elif score >= 5:
            risk_category = "HIGH_RISK"
            rebleed_risk = "20-40%"
            mortality_risk = "10-25%"
        elif score >= 3:
            risk_category = "MODERATE_RISK"
            rebleed_risk = "10-20%"
            mortality_risk = "3-10%"

        recommendation = f"Full Rockall Score: {score} ({risk_category}, Rebleed {rebleed_risk}, Mortality {mortality_risk}): Low risk for rebleeding; suitable for early outpatient discharge"
        if score >= 5:
            recommendation = f"HIGH-RISK ROCKALL SCORE: {score} ({risk_category}, Rebleed {rebleed_risk}, Mortality {mortality_risk}): Continue IV PPI infusion for 72 hours post-EBL/cautery; monitor for rebleeding requiring repeat EGD or embolization"

        return {
            "rockall_score": score,
            "risk_category": risk_category,
            "estimated_rebleed_risk": rebleed_risk,
            "estimated_30day_mortality": mortality_risk,
            "clinical_recommendation": recommendation,
            "status": "CALCULATION_COMPLETE",
        }


# Singleton engine instance
rockall_engine = UgibRockallScoreEngine()
