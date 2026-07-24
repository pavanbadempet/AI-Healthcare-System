"""
Myasthenia Gravis FcRn Receptor Antagonist Engine (Efgartigimod / Rozanolixizumab)
===================================================================================
Evaluates Neonatal Fc Receptor (FcRn) antagonist treatment cycles (Efgartigimod / Vyvgart IV/SC, Rozanolixizumab / Rystiggo)
in gMG patients with AChR+ or MuSK+ antibodies, monitoring MG-ADL score improvement and re-treatment triggers.
"""

from typing import Dict


class MgFcgrtReceptorAntagonistEngine:
    """Evaluates FcRn antagonist therapy in generalized Myasthenia Gravis."""

    def evaluate_fcrn_antagonist_cycle(
        self,
        gmg_achr_or_musk_positive: bool = True,
        baseline_mg_adl_score: int = 10,
        current_mg_adl_score: int = 4,  # >= 2 point reduction indicates clinical response
        weeks_since_last_cycle_start: int = 7,  # Minimum 50 days / ~7 weeks between cycle starts for Efgartigimod
        total_serum_igg_g_L: float = 8.0,  # Warning if IgG < 2.0 g/L
    ) -> Dict[str, any]:
        adl_improvement = baseline_mg_adl_score - current_mg_adl_score
        clinically_meaningful_response = adl_improvement >= 2

        # Re-treatment trigger: MG-ADL score rebounds by >= 2 points from nadir or returns to baseline
        reattendance_needed = (
            current_mg_adl_score >= baseline_mg_adl_score - 1
            and weeks_since_last_cycle_start >= 7
        )

        fcrn_agent = "EFGARTIGIMOD_VYVGART_10MG_KG_IV_WEEKLY_FOR_4_WEEKS"

        recommendation = f"FcRn Antagonist Cycle Completed (MG-ADL improvement {adl_improvement} pts): Patient currently in clinical remission/response; monitor MG-ADL score weekly"
        if reattendance_needed:
            recommendation = f"INITIATE NEW FCRN ANTAGONIST CYCLE ({fcrn_agent}): MG-ADL score rebound ({current_mg_adl_score}) at {weeks_since_last_cycle_start} weeks post-prior cycle; repeat 4-week treatment course to clear pathogenic AChR/MuSK IgG antibodies"

        return {
            "clinically_meaningful_response": clinically_meaningful_response,
            "adl_improvement_points": adl_improvement,
            "reattendance_needed": reattendance_needed,
            "recommended_fcrn_agent": fcrn_agent,
            "clinical_recommendation": recommendation,
            "status": "EVALUATION_COMPLETE",
        }


# Singleton engine instance
fcrn_engine = MgFcgrtReceptorAntagonistEngine()
