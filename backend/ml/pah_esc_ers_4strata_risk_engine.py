"""
Pulmonary Arterial Hypertension (PAH) ESC / ERS 4-Strata Risk Model Engine
===========================================================================
Stages PAH patients into 4 risk strata (Low, Intermediate-Low, Intermediate-High, High)
based on 2022 ESC/ERS guidelines incorporating WHO FC, 6MWD, and BNP/NT-proBNP.
"""

from typing import Dict, Optional


class PahEscErs4StrataRiskEngine:
    """Calculates 2022 ESC/ERS 4-Strata risk category for PAH mortality prediction."""

    def calculate_4strata_risk(
        self,
        who_functional_class: int,  # 1, 2, 3, 4
        six_minute_walk_distance_m: float,
        nt_pro_bnp_pg_mL: Optional[float] = None,
        bnp_pg_mL: Optional[float] = None,
    ) -> Dict[str, any]:
        # Scoring each variable from 1 (Low) to 4 (High)
        fc_score = 1
        if who_functional_class == 2:
            fc_score = 2
        elif who_functional_class == 3:
            fc_score = 3
        elif who_functional_class >= 4:
            fc_score = 4

        walk_score = 1
        if six_minute_walk_distance_m < 165.0:
            walk_score = 4
        elif six_minute_walk_distance_m <= 319.0:
            walk_score = 3
        elif six_minute_walk_distance_m <= 440.0:
            walk_score = 2

        bnp_score = 1
        if nt_pro_bnp_pg_mL is not None:
            if nt_pro_bnp_pg_mL > 1100.0:
                bnp_score = 4
            elif nt_pro_bnp_pg_mL >= 650.0:
                bnp_score = 3
            elif nt_pro_bnp_pg_mL >= 300.0:
                bnp_score = 2
        elif bnp_pg_mL is not None:
            if bnp_pg_mL > 800.0:
                bnp_score = 4
            elif bnp_pg_mL >= 200.0:
                bnp_score = 3
            elif bnp_pg_mL >= 50.0:
                bnp_score = 2

        mean_score = round((fc_score + walk_score + bnp_score) / 3.0, 2)

        risk_stratum = "LOW_RISK"
        mortality_1yr = "< 2.5%"
        treatment = "ORAL_DUAL_COMBINATION_ERA_AND_PDE5I"

        if mean_score >= 3.5:
            risk_stratum = "HIGH_RISK"
            mortality_1yr = "> 20%"
            treatment = "UPFRONT_TRIPLE_COMBINATION_WITH_INTRAVENOUS_EPOPROSTENOL"
        elif mean_score >= 2.5:
            risk_stratum = "INTERMEDIATE_HIGH_RISK"
            mortality_1yr = "10-20%"
            treatment = "ESCALATE_THERAPY_ADD_SELEXIPAG_OR_PARENTERAL_PROSTACYCLIN"
        elif mean_score >= 1.5:
            risk_stratum = "INTERMEDIATE_LOW_RISK"
            mortality_1yr = "5-10%"
            treatment = "SWITCH_PDE5I_TO_RIOCIGUAT_OR_ADD_SELEXIPAG"

        recommendation = f"ESC/ERS 4-Strata Mean Risk Score {mean_score} ({risk_stratum}, Estimated 1-year mortality {mortality_1yr}): {treatment}"

        return {
            "mean_risk_score": mean_score,
            "risk_stratum": risk_stratum,
            "estimated_1yr_mortality": mortality_1yr,
            "recommended_treatment": treatment,
            "clinical_recommendation": recommendation,
            "status": "CALCULATION_COMPLETE",
        }


# Singleton engine instance
pah_4strata_engine = PahEscErs4StrataRiskEngine()
