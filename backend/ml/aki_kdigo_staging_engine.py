"""
Acute Kidney Injury (AKI) KDIGO Staging Engine
===============================================
Stages AKI severity (Stage 1, Stage 2, Stage 3 / Dialysis) based on rolling 48-hour
serum creatinine fold increases and hourly urine output (mL/kg/h).
"""

from typing import Dict


class AkiKdigoStagingEngine:
    """Stages clinical Acute Kidney Injury according to KDIGO guidelines."""

    def stage_aki_progression(
        self,
        baseline_creatinine_mg_dL: float,
        current_creatinine_mg_dL: float,
        urine_output_mL_kg_hr_past_6hr: float,
    ) -> Dict[str, any]:
        creatinine_ratio = round(current_creatinine_mg_dL / max(baseline_creatinine_mg_dL, 0.1), 2)
        creatinine_delta = round(current_creatinine_mg_dL - baseline_creatinine_mg_dL, 2)

        stage = "STAGE_0_NO_AKI"
        recommendation = "Maintain hydration and standard renal function monitoring"

        if creatinine_ratio >= 3.0 or current_creatinine_mg_dL >= 4.0 or urine_output_mL_kg_hr_past_6hr < 0.3:
            stage = "STAGE_3_SEVERE_AKI"
            recommendation = "Urgent Nephrology Consult & consider Renal Replacement Therapy (RRT)"
        elif creatinine_ratio >= 2.0 or urine_output_mL_kg_hr_past_6hr < 0.5:
            stage = "STAGE_2_MODERATE_AKI"
            recommendation = "Discontinue nephrotoxic medications & optimize hemodynamics"
        elif creatinine_ratio >= 1.5 or creatinine_delta >= 0.3:
            stage = "STAGE_1_MILD_AKI"
            recommendation = "Close monitoring of fluid balance & daily serum creatinine"

        return {
            "baseline_creatinine": baseline_creatinine_mg_dL,
            "current_creatinine": current_creatinine_mg_dL,
            "creatinine_fold_increase": creatinine_ratio,
            "kdigo_aki_stage": stage,
            "clinical_recommendation": recommendation,
            "status": "STAGING_COMPLETE",
        }


# Singleton engine instance
aki_staging_engine = AkiKdigoStagingEngine()
