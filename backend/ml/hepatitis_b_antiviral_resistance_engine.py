"""
Chronic Hepatitis B Antiviral Resistance & Rescue Engine
=========================================================
Evaluates reverse transcriptase (rt) amino acid substitutions (rtM204V/I, rtL180M, rtA181T/V, rtN236T)
to detect resistance to Lamivudine, Entecavir, or Adefovir and select TAF/TDF rescue regimens.
"""

from typing import Dict, List


class HepatitisBAntiviralResistanceEngine:
    """Evaluates HBV RT resistance mutations and selects antiviral rescue therapy."""

    def evaluate_hbv_resistance(
        self,
        detected_mutations: List[str],  # e.g., ["rtM204V", "rtL180M", "rtA181T", "rtN236T"]
        current_antiviral: str = "ENTECAVIR",
        hbv_dna_viral_load_iu_mL: float = 1500.0,
    ) -> Dict[str, any]:
        lamivudine_resistant = any(m in detected_mutations for m in ["rtM204V", "rtM204I", "rtL180M"])
        entecavir_resistant = lamivudine_resistant and any(m in detected_mutations for m in ["rtI169T", "rtT184G", "rtS202I", "rtM250V"])
        adefovir_resistant = any(m in detected_mutations for m in ["rtA181T", "rtA181V", "rtN236T"])
        tenofovir_resistant = any(m in detected_mutations for m in ["rtA194T"])

        rescue_regimen = "CONTINUE_CURRENT_ANTIVIRAL_MONITOR_Q3M"
        resistance_detected = False

        if tenofovir_resistant or (entecavir_resistant and adefovir_resistant):
            rescue_regimen = "COMBINATION_RESCUE_TENOFOVIR_ALAFENAMIDE_TAF_25MG_PLUS_ENTECAVIR_1MG"
            resistance_detected = True
        elif entecavir_resistant or lamivudine_resistant:
            rescue_regimen = "SWITCH_TO_TENOFOVIR_ALAFENAMIDE_TAF_25MG_MONOTHERAPY"
            resistance_detected = True
        elif adefovir_resistant:
            rescue_regimen = "SWITCH_TO_ENTECAVIR_1MG_DAILY_OR_TAF_25MG"
            resistance_detected = True

        recommendation = "No RT resistance mutations detected; continue primary antiviral suppression & verify compliance"
        if resistance_detected:
            recommendation = f"HBV RT Resistance Detected ({', '.join(detected_mutations)}): Initiate {rescue_regimen}; recheck HBV DNA at 12 weeks to confirm viral decay"

        return {
            "detected_mutations": detected_mutations,
            "lamivudine_resistant": lamivudine_resistant,
            "entecavir_resistant": entecavir_resistant,
            "adefovir_resistant": adefovir_resistant,
            "resistance_detected": resistance_detected,
            "recommended_rescue_regimen": rescue_regimen,
            "clinical_recommendation": recommendation,
            "status": "EVALUATION_COMPLETE",
        }


# Singleton engine instance
hbv_resistance_engine = HepatitisBAntiviralResistanceEngine()
