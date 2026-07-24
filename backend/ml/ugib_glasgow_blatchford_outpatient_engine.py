"""
Acute Upper Gastrointestinal Bleeding (UGIB) Glasgow-Blatchford Outpatient Safety Engine
========================================================================================
Evaluates Glasgow-Blatchford Score (GBS <= 1 = safe for immediate outpatient discharge vs GBS >= 2 = inpatient admission).
"""

from typing import Dict


class UgibGlasgowBlatchfordOutpatientEngine:
    """Evaluates Glasgow-Blatchford score for safe outpatient discharge vs inpatient admission."""

    def evaluate_outpatient_safety(
        self,
        blood_urea_nitrogen_mg_dL: float,  # BUN score
        hemoglobin_g_dL: float,
        sex_male: bool = True,
        systolic_bp_mmHg: float = 120.0,
        pulse_bpm: float = 75.0,
        presentation_melena: bool = False,
        presentation_syncope: bool = False,
        hepatic_disease_present: bool = False,
        cardiac_failure_present: bool = False,
    ) -> Dict[str, any]:
        gbs_score = 0

        # BUN
        if blood_urea_nitrogen_mg_dL >= 70.0:
            gbs_score += 6
        elif blood_urea_nitrogen_mg_dL >= 28.0:
            gbs_score += 4
        elif blood_urea_nitrogen_mg_dL >= 22.4:
            gbs_score += 3
        elif blood_urea_nitrogen_mg_dL >= 18.2:
            gbs_score += 2

        # Hemoglobin (Male vs Female)
        if sex_male:
            if hemoglobin_g_dL < 10.0:
                gbs_score += 6
            elif hemoglobin_g_dL < 12.0:
                gbs_score += 3
            elif hemoglobin_g_dL < 13.0:
                gbs_score += 1
        else:
            if hemoglobin_g_dL < 10.0:
                gbs_score += 6
            elif hemoglobin_g_dL < 12.0:
                gbs_score += 1

        # Systolic BP
        if systolic_bp_mmHg < 100.0:
            gbs_score += 3
        elif systolic_bp_mmHg <= 109.0:
            gbs_score += 2
        elif systolic_bp_mmHg <= 119.0:
            gbs_score += 1

        # Other risk factors
        if pulse_bpm >= 100.0:
            gbs_score += 1
        if presentation_melena:
            gbs_score += 1
        if presentation_syncope:
            gbs_score += 2
        if hepatic_disease_present:
            gbs_score += 2
        if cardiac_failure_present:
            gbs_score += 2

        safe_for_outpatient_discharge = gbs_score <= 1

        recommendation = f"INPATIENT ADMISSION REQUIRED (GBS {gbs_score} >= 2): Admit for IV PPI therapy, fluid resuscitation, and inpatient EGD within 24 hours"
        if safe_for_outpatient_discharge:
            recommendation = f"SAFE FOR OUTPATIENT DISCHARGE (GBS {gbs_score} <= 1): Very low risk for intervention/mortality (< 0.5%); safe for outpatient endoscopy evaluation without inpatient hospital admission"

        return {
            "gbs_score": gbs_score,
            "safe_for_outpatient_discharge": safe_for_outpatient_discharge,
            "clinical_recommendation": recommendation,
            "status": "EVALUATION_COMPLETE",
        }


# Singleton engine instance
gbs_outpatient_engine = UgibGlasgowBlatchfordOutpatientEngine()
