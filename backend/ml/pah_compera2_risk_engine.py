"""
Pulmonary Arterial Hypertension (PAH) COMPERA 2.0 4-Strata Risk Engine
========================================================================
Calculates COMPERA 2.0 4-strata risk category (Low, Intermediate-Low, Intermediate-High, High)
based on European registry criteria incorporating WHO FC, 6MWD, and BNP/NT-proBNP.
"""

from typing import Dict, Optional


class PahCompera2RiskEngine:
    """Calculates COMPERA 2.0 4-strata risk score for PAH mortality prediction."""

    def calculate_compera2_risk(
        self,
        who_functional_class: int,  # 1, 2, 3, 4
        six_minute_walk_distance_m: float,
        bnp_pg_mL: Optional[float] = None,
        nt_pro_bnp_pg_mL: Optional[float] = None,
    ) -> Dict[str, any]:
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

        compera2_score = round((fc_score + walk_score + bnp_score) / 3.0, 2)

        risk_stratum = "LOW_RISK"
        mortality_1yr = "< 2.5%"
        therapy = "ORAL_DUAL_COMBINATION_ERA_AND_PDE5I"

        if compera2_score >= 3.5:
            risk_stratum = "HIGH_RISK"
            mortality_1yr = "> 20%"
            therapy = "UPFRONT_TRIPLE_COMBINATION_WITH_PARENTERAL_PROSTACYCLIN"
        elif compera2_score >= 2.5:
            risk_stratum = "INTERMEDIATE_HIGH_RISK"
            mortality_1yr = "10-20%"
            therapy = "ADD_ORAL_PROSTACYCLIN_RECEPTOR_AGONIST_SELEXIPAG"
        elif compera2_score >= 1.5:
            risk_stratum = "INTERMEDIATE_LOW_RISK"
            mortality_1yr = "5-10%"
            therapy = "OPTIMIZE_ORAL_DUAL_THERAPY_OR_SWITCH_TO_RIOCIGUAT"

        recommendation = f"COMPERA 2.0 4-Strata Score {compera2_score} ({risk_stratum}, 1-year mortality {mortality_1yr}): {therapy}"

        return {
            "compera2_score": compera2_score,
            "risk_stratum": risk_stratum,
            "estimated_1yr_mortality": mortality_1yr,
            "recommended_therapy": therapy,
            "clinical_recommendation": recommendation,
            "status": "CALCULATION_COMPLETE",
        }


# Singleton engine instance
compera2_engine = PahCompera2RiskEngine()
