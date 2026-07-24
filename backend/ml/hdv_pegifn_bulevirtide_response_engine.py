"""
Chronic Hepatitis Delta (HDV) PegIFN-Alpha vs Bulevirtide Response Engine
==========================================================================
Evaluates HDV RNA viral load drop (>= 2 log10 IU/mL decline at 24 weeks), ALT normalization,
and NTCP entry inhibitor Bulevirtide 2mg response to dictate 48-week vs 96-week extended duration.
"""

from typing import Dict


class HdvPegifnBulevirtideResponseEngine:
    """Evaluates Chronic Hepatitis Delta response to Bulevirtide and PegIFN-Alpha."""

    def evaluate_hdv_response(
        self,
        baseline_hdv_rna_iu_mL: float,
        week_24_hdv_rna_iu_mL: float,
        alt_u_L: float,
        bulevirtide_2mg_daily_active: bool = True,
        pegifn_alpha_active: bool = False,
    ) -> Dict[str, any]:
        import math

        log_drop = 0.0
        if baseline_hdv_rna_iu_mL > 0 and week_24_hdv_rna_iu_mL > 0:
            log_drop = math.log10(baseline_hdv_rna_iu_mL) - math.log10(week_24_hdv_rna_iu_mL)

        virological_response_24w = log_drop >= 2.0 or week_24_hdv_rna_iu_mL < 10.0
        biochemical_response = alt_u_L <= 35.0  # Normal ALT

        combined_response = virological_response_24w and biochemical_response

        recommendation = f"Suboptimal response at W24 (HDV RNA log drop {round(log_drop, 2)}): Intensify therapy with Bulevirtide 2 mg SC daily + PegIFN-alpha 180 mcg weekly for 48 weeks"
        if combined_response:
            recommendation = f"EXCELLENT COMBINED RESPONSE at W24 (HDV RNA log drop {round(log_drop, 2)}, ALT {alt_u_L} U/L): Continue Bulevirtide 2 mg daily for planned 48-week to 96-week duration; monitor HBsAg quantification"

        return {
            "hdv_rna_log10_decline": round(log_drop, 2),
            "virological_response_met": virological_response_24w,
            "biochemical_response_met": biochemical_response,
            "combined_response_achieved": combined_response,
            "clinical_recommendation": recommendation,
            "status": "EVALUATION_COMPLETE",
        }


# Singleton engine instance
hdv_response_engine = HdvPegifnBulevirtideResponseEngine()
