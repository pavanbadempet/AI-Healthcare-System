"""
Chronic Hepatitis B Antiviral Resistance & Rescue Therapy Engine
==================================================================
Evaluates viral breakthrough (HBV DNA rebound >= 1 log10 IU/mL) and polymerase gene mutations
(rtM204I/V, rtN236T, rtA181T/V) during NUC monotherapy to select high barrier rescue therapy.
"""

from typing import Dict


class HbvAntiviralResistanceRescueEngine:
    """Evaluates drug resistance mutations and rescue regimens in chronic hepatitis B."""

    def evaluate_rescue_therapy(
        self,
        current_nuc_regimen: str,  # LAMIVUDINE, ADEFOVIR, ENTECAVIR, TENOFOVIR
        viral_breakthrough_hbv_dna_iu_mL: float,  # > 2000 IU/mL after initial suppression
        rtM204V_or_I_lamivudine_mutation: bool = False,
        rtN236T_adefovir_mutation: bool = False,
        rtS202G_or_rtI169T_entecavir_mutation: bool = False,
    ) -> Dict[str, any]:
        resistance_detected = (
            rtM204V_or_I_lamivudine_mutation
            or rtN236T_adefovir_mutation
            or rtS202G_or_rtI169T_entecavir_mutation
            or viral_breakthrough_hbv_dna_iu_mL >= 2000.0
        )

        recommended_rescue = "CONTINUE_CURRENT_NUC_REGIMEN_AND_MONITOR_COMPLIANCE"

        if resistance_detected:
            if current_nuc_regimen.upper() in ["LAMIVUDINE", "TELBIVUDINE", "ENTECAVIR"]:
                recommended_rescue = "SWITCH_TO_TENOFOVIR_ALAFENAMIDE_TAF_OR_TDF_MONOTHERAPY"
            elif current_nuc_regimen.upper() == "ADEFOVIR":
                recommended_rescue = "SWITCH_TO_TENOFOVIR_ALAFENAMIDE_TAF_PLUS_ENTECAVIR_COMBINATION"
            elif current_nuc_regimen.upper() in ["TENOFOVIR", "TAF"]:
                recommended_rescue = "ADD_ENTECAVIR_TO_TAF_DUAL_COMBINATION_RESCUE"

        recommendation = f"No antiviral resistance detected; continue current {current_nuc_regimen} monotherapy"
        if resistance_detected:
            recommendation = f"ANTIVIRAL RESISTANCE / VIRAL BREAKTHROUGH DETECTED (HBV DNA {viral_breakthrough_hbv_dna_iu_mL} IU/mL): Switch/Add rescue regimen -> {recommended_rescue}. High genetic barrier agents (TAF 25 mg daily or TDF 300 mg daily) suppress multidrug resistant HBV variants"

        return {
            "current_nuc_regimen": current_nuc_regimen,
            "resistance_or_breakthrough_detected": resistance_detected,
            "recommended_rescue_regimen": recommended_rescue,
            "clinical_recommendation": recommendation,
            "status": "EVALUATION_COMPLETE",
        }


# Singleton engine instance
hbv_resistance_engine = HbvAntiviralResistanceRescueEngine()
