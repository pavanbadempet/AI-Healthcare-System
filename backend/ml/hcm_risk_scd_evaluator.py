"""
Hypertrophic Cardiomyopathy (HCM) Risk-SCD Evaluator
=====================================================
Evaluates 5-year Sudden Cardiac Death (SCD) risk in hypertrophic cardiomyopathy patients.
"""

import math
from typing import Dict


class HcmRiskScdEvaluator:
    """Calculates ESC HCM Risk-SCD 5-year mortality and ICD indication."""

    def calculate_hcm_risk_scd(
        self,
        max_left_ventricular_wall_thickness_mm: float,
        left_atrial_diameter_mm: float,
        max_lv_outflow_tract_gradient_mmHg: float,
        family_history_scd: bool,
        non_sustained_ventricular_tachycardia_nsvt: bool,
        unexplained_syncope: bool,
        age_years: int,
    ) -> Dict[str, any]:
        # ESC 5-Year Risk-SCD formula predictor linear score
        prognostic_score = (
            0.1593 * max_left_ventricular_wall_thickness_mm
            - 0.00294 * (max_left_ventricular_wall_thickness_mm ** 2)
            + 0.0259 * left_atrial_diameter_mm
            + 0.0041 * max_lv_outflow_tract_gradient_mmHg
            + 0.749 * (1 if family_history_scd else 0)
            + 0.426 * (1 if non_sustained_ventricular_tachycardia_nsvt else 0)
            + 0.331 * (1 if unexplained_syncope else 0)
            - 0.015 * age_years
        )

        five_year_risk_pct = round((1.0 - (0.998 ** math.exp(prognostic_score))) * 100, 1)

        icd_recommendation = "Low risk (<4%); ICD generally not indicated"
        if five_year_risk_pct >= 6.0:
            icd_recommendation = "High risk (>=6%); Prophylactic Primary Prevention ICD implantation recommended (Class I)"
        elif five_year_risk_pct >= 4.0:
            icd_recommendation = "Intermediate risk (4-6%); ICD implantation may be considered (Class IIa)"

        return {
            "five_year_scd_risk_percent": five_year_risk_pct,
            "risk_tier": "HIGH_RISK" if five_year_risk_pct >= 6.0 else ("INTERMEDIATE_RISK" if five_year_risk_pct >= 4.0 else "LOW_RISK"),
            "primary_prevention_icd_indicated": five_year_risk_pct >= 4.0,
            "esc_guideline_recommendation": icd_recommendation,
            "status": "EVALUATION_COMPLETE",
        }


# Singleton evaluator instance
hcm_scd_evaluator = HcmRiskScdEvaluator()
