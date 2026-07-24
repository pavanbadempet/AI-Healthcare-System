"""
COPD BODE Index Predictor
=========================
Calculates BODE Index (BMI, FEV1, MMRC Dyspnea, 6MWD: 0-10 points) for COPD mortality estimation.
"""

from typing import Dict


class CopdBodeIndexEngine:
    """Calculates BODE Index for COPD 4-year mortality prediction."""

    def calculate_bode_index(
        self,
        body_mass_index: float,
        fev1_percent_predicted: float,
        mmrc_dyspnea_grade: int,  # 0 to 4
        six_minute_walk_distance_meters: float,
    ) -> Dict[str, any]:
        score = 0

        # BMI B
        if body_mass_index <= 21.0:
            score += 1

        # Obstruction O (FEV1)
        if fev1_percent_predicted < 36.0:
            score += 3
        elif fev1_percent_predicted < 50.0:
            score += 2
        elif fev1_percent_predicted < 65.0:
            score += 1

        # Dyspnea D (MMRC)
        if mmrc_dyspnea_grade == 4:
            score += 3
        elif mmrc_dyspnea_grade == 3:
            score += 2
        elif mmrc_dyspnea_grade == 2:
            score += 1

        # Exercise E (6MWD)
        if six_minute_walk_distance_meters < 150:
            score += 3
        elif six_minute_walk_distance_meters < 250:
            score += 2
        elif six_minute_walk_distance_meters < 350:
            score += 1

        four_year_mortality_pct = 18.0
        if score >= 7:
            four_year_mortality_pct = 80.0
        elif score >= 5:
            four_year_mortality_pct = 57.0
        elif score >= 3:
            four_year_mortality_pct = 32.0

        recommendation = "BODE 0-2: Low mortality risk; maintain LAMA/LABA inhaler therapy & pulmonary rehab"
        if score >= 7:
            recommendation = "BODE 7-10: High 4-year mortality (80%); evaluate triple inhaler (ICS/LAMA/LABA), long-term O2, & lung volume reduction"

        return {
            "bode_index_score": score,
            "four_year_mortality_percent": four_year_mortality_pct,
            "high_mortality_risk": score >= 7,
            "clinical_recommendation": recommendation,
            "status": "CALCULATION_COMPLETE",
        }


# Singleton engine instance
copd_bode_engine = CopdBodeIndexEngine()
