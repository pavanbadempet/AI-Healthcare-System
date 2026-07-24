"""
Autoimmune Hepatitis (AIH) Simplified IAIHG Diagnostic Engine
==============================================================
Scores IgG, Autoantibodies (ANA/SMA/anti-LKM-1/anti-SLA), Liver Histology,
and Viral Hepatitis Exclusion for AIH diagnostic classification.
"""

from typing import Dict


class AihIaihgSimplifiedEngine:
    """Calculates Simplified IAIHG score (0-8) for Autoimmune Hepatitis diagnosis."""

    def calculate_aih_score(
        self,
        autoantibodies_ana_or_sma_titer: str,  # "NONE", ">=1:40", ">=1:80", "anti_LKM1_>=1:40", "anti_SLA_positive"
        igg_level_relative_to_uln: str,        # "NORMAL", ">1.0x", ">1.10x"
        liver_histology_typical_or_compatible: str,  # "NONE", "COMPATIBLE", "TYPICAL"
        viral_hepatitis_excluded: bool,        # HAV, HBV, HCV serologies negative
    ) -> Dict[str, any]:
        score = 0

        # Autoantibodies (max 2 points)
        if autoantibodies_ana_or_sma_titer in [">=1:80", "anti_LKM1_>=1:40", "anti_SLA_positive"]:
            score += 2
        elif autoantibodies_ana_or_sma_titer == ">=1:40":
            score += 1

        # IgG (max 2 points)
        if igg_level_relative_to_uln == ">1.10x":
            score += 2
        elif igg_level_relative_to_uln == ">1.0x":
            score += 1

        # Histology (max 2 points)
        if liver_histology_typical_or_compatible == "TYPICAL":
            score += 2
        elif liver_histology_typical_or_compatible == "COMPATIBLE":
            score += 1

        # Viral exclusion (2 points)
        if viral_hepatitis_excluded:
            score += 2

        diagnosis = "UNLIKELY_AIH"
        corticosteroids_indicated = False

        if score >= 7:
            diagnosis = "DEFINITE_AUTOIMMUNE_HEPATITIS"
            corticosteroids_indicated = True
        elif score >= 6:
            diagnosis = "PROBABLE_AUTOIMMUNE_HEPATITIS"
            corticosteroids_indicated = True

        recommendation = "Score < 6: AIH unlikely; investigate metabolic, drug-induced, or cholestatic liver diseases"
        if corticosteroids_indicated:
            recommendation = "Simplified IAIHG Score >= 6: Initiate immunosuppressive therapy (Prednisolone/Budesonide + Azathioprine)"

        return {
            "iaihg_total_score": score,
            "aih_diagnosis": diagnosis,
            "immunosuppressive_therapy_indicated": corticosteroids_indicated,
            "clinical_recommendation": recommendation,
            "status": "CALCULATION_COMPLETE",
        }


# Singleton engine instance
aih_iaihg_engine = AihIaihgSimplifiedEngine()
