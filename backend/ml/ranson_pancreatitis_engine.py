"""
Acute Pancreatitis Ranson Criteria 48-Hour Mortality Engine
============================================================
Calculates 0-hour and 48-hour Ranson scores (11 parameters) for acute pancreatitis mortality prediction.
"""

from typing import Dict, Optional


class RansonPancreatitisEngine:
    """Calculates 0h and 48h Ranson Criteria score for acute pancreatitis."""

    def calculate_ranson_score(
        self,
        age_years: int,
        wbc_count_10_3_ul: float,
        blood_glucose_mg_dL: float,
        ast_u_l: float,
        ldh_u_l: float,
        hematocrit_drop_percent_48h: Optional[float] = None,
        bun_rise_mg_dL_48h: Optional[float] = None,
        serum_calcium_mg_dL_48h: Optional[float] = None,
        pao2_mmHg_48h: Optional[float] = None,
        base_deficit_mEq_L_48h: Optional[float] = None,
        estimated_fluid_sequestration_L_48h: Optional[float] = None,
    ) -> Dict[str, any]:
        score = 0

        # At Admission (0h)
        if age_years > 55:
            score += 1
        if wbc_count_10_3_ul > 16.0:
            score += 1
        if blood_glucose_mg_dL > 200.0:
            score += 1
        if ast_u_l > 250.0:
            score += 1
        if ldh_u_l > 350.0:
            score += 1

        # At 48 Hours
        if hematocrit_drop_percent_48h is not None and hematocrit_drop_percent_48h > 10.0:
            score += 1
        if bun_rise_mg_dL_48h is not None and bun_rise_mg_dL_48h > 5.0:
            score += 1
        if serum_calcium_mg_dL_48h is not None and serum_calcium_mg_dL_48h < 8.0:
            score += 1
        if pao2_mmHg_48h is not None and pao2_mmHg_48h < 60.0:
            score += 1
        if base_deficit_mEq_L_48h is not None and base_deficit_mEq_L_48h > 4.0:
            score += 1
        if estimated_fluid_sequestration_L_48h is not None and estimated_fluid_sequestration_L_48h > 6.0:
            score += 1

        mortality_pct = 1.0
        if score >= 7:
            mortality_pct = 50.0
        elif score >= 5:
            mortality_pct = 40.0
        elif score >= 3:
            mortality_pct = 15.0

        icu_admission = score >= 3

        recommendation = "Ranson < 3: Low mortality risk (1%); standard ward admission & aggressive crystalloid hydration"
        if score >= 5:
            recommendation = "Ranson >= 5: High mortality (40-50%); STAT ICU admission, invasive arterial/CVP monitoring, & surgical GI consult"
        elif icu_admission:
            recommendation = "Ranson 3-4: Severe acute pancreatitis (15% mortality); Step-down / ICU monitoring indicated"

        return {
            "ranson_total_score": score,
            "estimated_mortality_percent": mortality_pct,
            "severe_pancreatitis_present": icu_admission,
            "icu_admission_indicated": icu_admission,
            "clinical_recommendation": recommendation,
            "status": "CALCULATION_COMPLETE",
        }


# Singleton engine instance
ranson_pancreatitis_engine = RansonPancreatitisEngine()
