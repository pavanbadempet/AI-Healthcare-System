"""
Autoimmune Hepatitis (AIH) Simplified IAIHG Scoring Engine
===========================================================
Evaluates 2008 Simplified International Autoimmune Hepatitis Group (IAIHG) criteria
(ANA/SMA titers, serum IgG, liver histology, viral markers) to diagnose Definite vs Probable AIH.
"""

from typing import Dict


class AutoimmuneHepatitisIaihgEngine:
    """Evaluates 2008 Simplified IAIHG diagnostic criteria for Autoimmune Hepatitis."""

    def evaluate_simplified_iaihg_score(
        self,
        ana_or_sma_titer: str,  # NEGATIVE, TITER_1_40, TITER_1_80_OR_HIGHER
        lkm1_titer_1_40_or_higher: bool = False,
        sla_lp_positive: bool = False,
        serum_igg_level: str = "NORMAL",  # NORMAL, ELEVATED_ABOVE_ULN, ELEVATED_1_10_TIMES_ULN
        histology_features: str = "TYPICAL",  # ATYPICAL, COMPATIBLE, TYPICAL
        viral_hepatitis_excluded: bool = True,  # HAV, HBV, HCV excluded
    ) -> Dict[str, any]:
        score = 0

        # Autoantibodies
        if sla_lp_positive or ana_or_sma_titer == "TITER_1_80_OR_HIGHER" or lkm1_titer_1_40_or_higher:
            score += 2
        elif ana_or_sma_titer == "TITER_1_40":
            score += 1

        # IgG
        if serum_igg_level in ["ELEVATED_ABOVE_ULN", "ELEVATED_1_10_TIMES_ULN"]:
            score += 2 if serum_igg_level == "ELEVATED_1_10_TIMES_ULN" else 1

        # Histology
        if histology_features == "TYPICAL":
            score += 2
        elif histology_features == "COMPATIBLE":
            score += 1

        # Viral Hepatitis
        if viral_hepatitis_excluded:
            score += 2

        diagnosis = "UNLIKELY_AUTOIMMUNE_HEPATITIS"
        therapy_indicated = False

        if score >= 7:
            diagnosis = "DEFINITE_AUTOIMMUNE_HEPATITIS"
            therapy_indicated = True
        elif score == 6:
            diagnosis = "PROBABLE_AUTOIMMUNE_HEPATITIS"
            therapy_indicated = True

        recommendation = f"Simplified IAIHG Score: {score} ({diagnosis}): Initiate dual immunosuppressive therapy with Prednisolone (1 mg/kg/day) + Azathioprine (1-2 mg/kg/day)"
        if not therapy_indicated:
            recommendation = f"Simplified IAIHG Score: {score} ({diagnosis}): AIH criteria not met; investigate alternative etiologies (DILI, NASH, Wilson's disease)"

        return {
            "iaihg_score": score,
            "diagnosis": diagnosis,
            "immunosuppressive_therapy_indicated": therapy_indicated,
            "clinical_recommendation": recommendation,
            "status": "EVALUATION_COMPLETE",
        }


# Singleton engine instance
aih_iaihg_engine = AutoimmuneHepatitisIaihgEngine()
