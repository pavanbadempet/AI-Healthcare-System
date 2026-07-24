"""
Pulmonary Arterial Hypertension (PAH) REVEAL 2.0 Risk Score Engine
===================================================================
Calculates the REVEAL 2.0 Risk Score based on WHO Functional Class, 6MWD, BNP/NT-proBNP,
RAP, PVR, and eGFR to categorize 1-year mortality risk (Low <= 6, Intermediate 7-8, High >= 9)
and direct combination vasodilator therapy (ERA + PDE5i + Prostacyclin).
"""

from typing import Dict, Optional


class PahReveal2RiskEngine:
    """Calculates REVEAL 2.0 risk score for Pulmonary Arterial Hypertension (Group 1 PAH)."""

    def calculate_reveal2_score(
        self,
        who_functional_class: int,  # 1, 2, 3, 4
        six_minute_walk_distance_m: float,
        bnp_pg_mL: Optional[float] = None,
        nt_pro_bnp_pg_mL: Optional[float] = None,
        right_atrial_pressure_mmHg: Optional[float] = None,
        pulmonary_vascular_resistance_wood_units: Optional[float] = None,
        egfr_mL_min_1_73m2: Optional[float] = None,
        male_over_60: bool = False,
    ) -> Dict[str, any]:
        score = 0

        # Subtype / Demographics
        if male_over_60:
            score += 2

        # WHO Functional Class
        if who_functional_class == 1:
            score -= 1
        elif who_functional_class == 3:
            score += 1
        elif who_functional_class == 4:
            score += 2

        # 6MWD
        if six_minute_walk_distance_m >= 440.0:
            score -= 1
        elif six_minute_walk_distance_m < 165.0:
            score += 2
        elif six_minute_walk_distance_m < 320.0:
            score += 1

        # BNP / NT-proBNP
        if nt_pro_bnp_pg_mL is not None:
            if nt_pro_bnp_pg_mL < 300.0:
                score -= 1
            elif nt_pro_bnp_pg_mL > 1100.0:
                score += 2
            elif nt_pro_bnp_pg_mL > 300.0:
                score += 1
        elif bnp_pg_mL is not None:
            if bnp_pg_mL < 50.0:
                score -= 1
            elif bnp_pg_mL > 180.0:
                score += 2

        # Hemodynamics
        if right_atrial_pressure_mmHg is not None and right_atrial_pressure_mmHg > 14.0:
            score += 1
        if pulmonary_vascular_resistance_wood_units is not None and pulmonary_vascular_resistance_wood_units > 10.0:
            score += 1

        # Renal function
        if egfr_mL_min_1_73m2 is not None and egfr_mL_min_1_73m2 < 60.0:
            score += 1

        risk_category = "LOW_RISK"
        mortality_1yr_pct = "< 2.5%"
        therapy = "ORAL_DUAL_COMBINATION_ERA_AND_PDE5I"

        if score >= 9:
            risk_category = "HIGH_RISK"
            mortality_1yr_pct = "> 10%"
            therapy = "TRIPLE_COMBINATION_INCLUDING_PARENTERAL_PROSTACYCLIN_EPOPROSTENOL"
        elif score >= 7:
            risk_category = "INTERMEDIATE_RISK"
            mortality_1yr_pct = "5-10%"
            therapy = "ADD_ORAL_PROSTACYCLIN_RECEPTOR_AGONIST_SELEXIPAG"

        recommendation = f"PAH REVEAL 2.0 Score {score} ({risk_category}, 1-year mortality {mortality_1yr_pct}): Initiate {therapy}"

        return {
            "reveal2_score": score,
            "risk_category": risk_category,
            "estimated_1yr_mortality": mortality_1yr_pct,
            "recommended_therapy": therapy,
            "clinical_recommendation": recommendation,
            "status": "CALCULATION_COMPLETE",
        }


# Singleton engine instance
pah_reveal_engine = PahReveal2RiskEngine()
