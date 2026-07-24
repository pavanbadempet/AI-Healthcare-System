"""
Heart Failure MAGGIC Mortality & Survival Predictor
===================================================
Calculates 1-year and 3-year mortality probability for heart failure patients
based on ejection fraction, NYHA functional class, blood pressure, creatinine, and GDMT usage.
"""

from typing import Dict


class MaggicHeartFailureModel:
    """Calculates MAGGIC risk score and survival probability in heart failure."""

    def calculate_maggic_mortality(
        self,
        ejection_fraction_percent: int,
        nyha_class: int,  # 1 to 4
        systolic_bp_mmHg: int,
        age_years: int,
        creatinine_mg_dL: float,
        on_beta_blocker: bool = True,
        on_acei_arb_arni: bool = True,
    ) -> Dict[str, any]:
        # MAGGIC score calculation
        score = 0
        if ejection_fraction_percent < 30:
            score += 7
        elif ejection_fraction_percent < 40:
            score += 3

        score += (nyha_class - 1) * 3

        if systolic_bp_mmHg < 110:
            score += 5

        if age_years > 70:
            score += 6
        elif age_years > 60:
            score += 3

        if creatinine_mg_dL > 2.0:
            score += 4

        if not on_beta_blocker:
            score += 3
        if not on_acei_arb_arni:
            score += 3

        one_year_mortality_pct = round(min(score * 0.8, 40.0), 1)
        three_year_mortality_pct = round(min(score * 1.8, 75.0), 1)

        return {
            "maggic_score": score,
            "one_year_mortality_risk_percent": one_year_mortality_pct,
            "three_year_mortality_risk_percent": three_year_mortality_pct,
            "guideline_directed_medical_therapy_optimized": on_beta_blocker and on_acei_arb_arni,
            "status": "PREDICTION_COMPLETE",
        }


# Singleton model instance
maggic_model = MaggicHeartFailureModel()
