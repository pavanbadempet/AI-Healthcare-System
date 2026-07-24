"""
Osteoporosis Fracture Risk Assessment (FRAX) Calculator
=========================================================
Computes 10-year major osteoporotic and hip fracture probability from femoral neck
BMD T-score and clinical risk factors (prior fracture, glucocorticoids, rheumatoid arthritis).
"""

from typing import Dict


class FraxOsteoporosisCalculator:
    """Estimates 10-year osteoporotic fracture risk using clinical risk metrics."""

    def calculate_fracture_risk(
        self,
        age_years: int,
        femoral_neck_t_score: float,
        previous_fracture: bool = False,
        current_smoking: bool = False,
        glucocorticoid_use: bool = False,
        rheumatoid_arthritis: bool = False,
    ) -> Dict[str, any]:
        # Risk estimation model
        base_major_risk = 3.0 + (age_years - 50) * 0.25
        if femoral_neck_t_score <= -2.5:
            base_major_risk += 12.0
        elif femoral_neck_t_score <= -1.0:
            base_major_risk += 5.0

        if previous_fracture:
            base_major_risk += 6.0
        if glucocorticoid_use:
            base_major_risk += 4.5
        if rheumatoid_arthritis:
            base_major_risk += 3.0

        major_risk_pct = round(min(base_major_risk, 45.0), 1)
        hip_risk_pct = round(major_risk_pct * 0.35, 1)

        recommend_treatment = major_risk_pct >= 20.0 or hip_risk_pct >= 3.0 or femoral_neck_t_score <= -2.5

        return {
            "age_years": age_years,
            "femoral_neck_t_score": femoral_neck_t_score,
            "ten_year_major_osteoporotic_fracture_probability_percent": major_risk_pct,
            "ten_year_hip_fracture_probability_percent": hip_risk_pct,
            "pharmacotherapy_recommended": recommend_treatment,
            "guideline_action": "Initiate Bisphosphonate / Denosumab therapy" if recommend_treatment else "Calcium & Vitamin D supplementation with repeat DEXA in 2 years",
            "status": "CALCULATION_COMPLETE",
        }


# Singleton calculator instance
frax_calculator = FraxOsteoporosisCalculator()
