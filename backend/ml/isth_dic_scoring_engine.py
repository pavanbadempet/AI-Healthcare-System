"""
Disseminated Intravascular Coagulation (DIC) ISTH Scoring Engine
===================================================================
Computes ISTH overt DIC score (Platelets, Fibrin degradation products / D-Dimer, Prolonged PT, Fibrinogen)
for critical care coagulopathy monitoring.
"""

from typing import Dict


class IsthDicScoringEngine:
    """Calculates ISTH score for overt DIC diagnostic criteria."""

    def calculate_isth_dic_score(
        self,
        platelet_count_k_uL: int,
        elevated_fdp_d_dimer: str,  # 'NONE', 'MODERATE', 'STRONG'
        prolonged_pt_seconds: float,
        fibrinogen_g_L: float,
    ) -> Dict[str, any]:
        score = 0
        if platelet_count_k_uL < 50:
            score += 2
        elif platelet_count_k_uL < 100:
            score += 1

        if elevated_fdp_d_dimer.upper() == "STRONG":
            score += 3
        elif elevated_fdp_d_dimer.upper() == "MODERATE":
            score += 2

        if prolonged_pt_seconds >= 6.0:
            score += 2
        elif prolonged_pt_seconds >= 3.0:
            score += 1

        if fibrinogen_g_L < 1.0:
            score += 1

        overt_dic = score >= 5

        return {
            "isth_dic_score": score,
            "overt_dic_present": overt_dic,
            "clinical_recommendation": "Compatible with overt DIC: Treat underlying cause & administer Cryoprecipitate / FFP / Platelets stat" if overt_dic else "Non-overt DIC: Repeat scoring daily",
            "status": "SCORING_COMPLETE",
        }


# Singleton engine instance
isth_dic_engine = IsthDicScoringEngine()
