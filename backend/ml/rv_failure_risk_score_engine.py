"""
Invasive Right Ventricular Failure Risk Score (RVFRS) Engine
==============================================================
Calculates RVFRS score post-LVAD implantation (RAP/PCWP > 0.63, PAPi < 1.85, vasopressors)
to predict right ventricular failure and RVAD indication.
"""

from typing import Dict


class RvFailureRiskScoreEngine:
    """Evaluates RV failure risk post-LVAD implantation using invasive hemodynamics."""

    def calculate_rvfrs_score(
        self,
        rap_pcwp_ratio: float,                     # RAP / PCWP (> 0.63 is +2)
        pulmonary_artery_pulsatility_index_papi: float, # PAPi = (PASP - PADP) / RAP (< 1.85 is +2)
        preop_vasopressors_count: int,             # >=2 is +1
        preop_ast_u_l: float = 35.0,              # >80 U/L is +1
    ) -> Dict[str, any]:
        score = 0

        if rap_pcwp_ratio > 0.63:
            score += 2

        if pulmonary_artery_pulsatility_index_papi < 1.85:
            score += 2

        if preop_vasopressors_count >= 2:
            score += 1

        if preop_ast_u_l > 80.0:
            score += 1

        rv_failure_risk_pct = 8.0
        if score >= 4:
            rv_failure_risk_pct = 48.0
        elif score >= 2:
            rv_failure_risk_pct = 22.0

        rvad_indicated = score >= 4

        recommendation = "Low RV failure risk (<10%); standard post-LVAD ICU care & Inotrope weaning"
        if rvad_indicated:
            recommendation = "High RV Failure Risk (48%): Prepare Right Ventricular Assist Device (RVAD / Impella RP) & inhaled Epoprostenol / Milrinone"

        return {
            "rvfrs_total_score": score,
            "rv_failure_risk_percent": rv_failure_risk_pct,
            "rvad_support_indicated": rvad_indicated,
            "clinical_recommendation": recommendation,
            "status": "SCORING_COMPLETE",
        }


# Singleton engine instance
rvfrs_engine = RvFailureRiskScoreEngine()
