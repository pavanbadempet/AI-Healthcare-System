"""
Hypertrophic Cardiomyopathy (HCM) Risk-SCD 5-Year Mortality Model
==================================================================
Computes ESC HCM Risk-SCD 5-year sudden cardiac death risk percentage
to guide ICD primary prevention decision-making.
"""

import math
from typing import Dict


class HcmRiskScdModel:
    """Calculates HCM Risk-SCD 5-year sudden cardiac death probability."""

    def calculate_hcm_scd_risk(
        self,
        max_lv_wall_thickness_mm: float,
        left_atrial_diameter_mm: float,
        max_lvot_gradient_mmHg: float,
        family_history_scd: bool,
        non_sustained_vt: bool,
        unexplained_syncope: bool,
        age_years: int,
    ) -> Dict[str, any]:
        # ESC HCM Risk-SCD prognostic index calculation model
        wt = min(max_lv_wall_thickness_mm, 30.0)
        prognostic_index = (
            0.154 * wt
            - 0.002 * (wt ** 2)
            + 0.045 * left_atrial_diameter_mm
            + 0.004 * max_lvot_gradient_mmHg
            + 0.769 * (1 if family_history_scd else 0)
            + 0.859 * (1 if non_sustained_vt else 0)
            + 0.495 * (1 if unexplained_syncope else 0)
            - 0.017 * age_years
        )

        five_year_risk_pct = round((1 - (0.998 ** math.exp(prognostic_index))) * 100, 1)

        icd_recommendation = "ICD not generally recommended"
        if five_year_risk_pct >= 6.0:
            icd_recommendation = "ICD implantation should be considered (High Risk >= 6%)"
        elif five_year_risk_pct >= 4.0:
            icd_recommendation = "ICD implantation may be considered (Intermediate Risk 4-6%)"

        return {
            "five_year_scd_risk_percent": five_year_risk_pct,
            "esc_risk_category": "HIGH_RISK" if five_year_risk_pct >= 6.0 else ("INTERMEDIATE_RISK" if five_year_risk_pct >= 4.0 else "LOW_RISK"),
            "icd_recommendation": icd_recommendation,
            "primary_prevention_icd_indicated": five_year_risk_pct >= 6.0,
            "status": "PREDICTION_COMPLETE",
        }


# Singleton model instance
hcm_scd_model = HcmRiskScdModel()
