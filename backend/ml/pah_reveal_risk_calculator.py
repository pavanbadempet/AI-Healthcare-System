"""
Idiopathic Pulmonary Arterial Hypertension (PAH) REVEAL 2.0 Risk Calculator
=============================================================================
Calculates REVEAL 2.0 risk score and 1-year mortality for Pulmonary Arterial Hypertension.
"""

from typing import Dict


class PahRevealRiskCalculator:
    """Calculates REVEAL 2.0 score for Pulmonary Arterial Hypertension risk estimation."""

    def calculate_reveal_score(
        self,
        nyha_functional_class: int,  # 1 to 4
        six_minute_walk_distance_meters: float,
        nt_probnp_pg_mL: float,
        right_atrial_pressure_mmHg: float,
        pulmonary_vascular_resistance_wood_units: float,
    ) -> Dict[str, any]:
        score = 0

        # NYHA FC
        if nyha_functional_class == 4:
            score += 2
        elif nyha_functional_class == 3:
            score += 1

        # 6MWD
        if six_minute_walk_distance_meters < 165:
            score += 2
        elif six_minute_walk_distance_meters < 330:
            score += 1

        # NT-proBNP
        if nt_probnp_pg_mL > 1100:
            score += 2
        elif nt_probnp_pg_mL > 300:
            score += 1

        # Hemodynamics
        if right_atrial_pressure_mmHg > 14:
            score += 1
        if pulmonary_vascular_resistance_wood_units > 10:
            score += 1

        risk_category = "LOW_RISK"
        one_year_mortality_pct = 2.0

        if score >= 9:
            risk_category = "HIGH_RISK"
            one_year_mortality_pct = 22.0
        elif score >= 7:
            risk_category = "INTERMEDIATE_HIGH_RISK"
            one_year_mortality_pct = 12.0
        elif score >= 5:
            risk_category = "INTERMEDIATE_LOW_RISK"
            one_year_mortality_pct = 5.0

        return {
            "reveal_2_0_score": score,
            "pah_risk_category": risk_category,
            "one_year_mortality_risk_percent": one_year_mortality_pct,
            "triple_combination_therapy_indicated": risk_category in ["HIGH_RISK", "INTERMEDIATE_HIGH_RISK"],
            "status": "CALCULATION_COMPLETE",
        }


# Singleton calculator instance
pah_reveal_calculator = PahRevealRiskCalculator()
