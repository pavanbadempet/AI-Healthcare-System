"""
Acute Upper Gastrointestinal Bleed (UGIB) Glasgow-Blatchford Score (GBS) Engine
================================================================================
Calculates Glasgow-Blatchford Score (GBS, 0-23) based on BUN, Hemoglobin, Systolic BP,
Heart Rate, Melena, Syncope, and Comorbidities to identify ultra-low risk patients (GBS <= 1)
suitable for outpatient discharge vs high risk needing urgent EGD within 12h.
"""

from typing import Dict


class UgibGlasgowBlatchfordEngine:
    """Calculates Glasgow-Blatchford Score for Acute Upper GI Bleeding."""

    def calculate_gbs(
        self,
        bun_mg_dL: float,
        hemoglobin_g_dL: float,
        systolic_bp_mmHg: float,
        heart_rate_bpm: float,
        is_female: bool = False,
        melena_present: bool = False,
        syncope_present: bool = False,
        hepatic_disease_history: bool = False,
        cardiac_failure_history: bool = False,
    ) -> Dict[str, any]:
        score = 0

        # BUN scoring
        if bun_mg_dL >= 70.0:
            score += 6
        elif bun_mg_dL >= 28.0:
            score += 4
        elif bun_mg_dL >= 22.4:
            score += 3
        elif bun_mg_dL >= 18.2:
            score += 2

        # Hemoglobin scoring
        if is_female:
            if hemoglobin_g_dL < 10.0:
                score += 6
            elif hemoglobin_g_dL < 12.0:
                score += 1
        else:
            if hemoglobin_g_dL < 10.0:
                score += 6
            elif hemoglobin_g_dL < 12.0:
                score += 3
            elif hemoglobin_g_dL < 13.0:
                score += 1

        # Systolic BP
        if systolic_bp_mmHg < 90.0:
            score += 3
        elif systolic_bp_mmHg <= 99.0:
            score += 2
        elif systolic_bp_mmHg <= 109.0:
            score += 1

        # Heart rate
        if heart_rate_bpm >= 100.0:
            score += 1

        # Clinical presentations & comorbidities
        if melena_present:
            score += 1
        if syncope_present:
            score += 2
        if hepatic_disease_history:
            score += 2
        if cardiac_failure_history:
            score += 2

        risk_category = "HIGH_RISK"
        outpatient_discharge_safe = False
        egd_urgency = "INPATIENT_URGENT_EGD_WITHIN_12_HOURS"

        if score <= 1:
            risk_category = "VERY_LOW_RISK"
            outpatient_discharge_safe = True
            egd_urgency = "OUTPATIENT_ELECTIVE_EGD_OR_DISCHARGE"
        elif score <= 6:
            risk_category = "INTERMEDIATE_RISK"
            egd_urgency = "INPATIENT_EGD_WITHIN_24_HOURS"

        recommendation = f"Glasgow-Blatchford Score {score} ({risk_category}): {egd_urgency}"

        return {
            "glasgow_blatchford_score": score,
            "risk_category": risk_category,
            "outpatient_discharge_safe": outpatient_discharge_safe,
            "recommended_egd_urgency": egd_urgency,
            "clinical_recommendation": recommendation,
            "status": "CALCULATION_COMPLETE",
        }


# Singleton engine instance
gbs_engine = UgibGlasgowBlatchfordEngine()
