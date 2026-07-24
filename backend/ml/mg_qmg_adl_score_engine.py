"""
Myasthenia Gravis Quantitative MG (QMG) & MG-ADL Score Engine
==============================================================
Evaluates QMG clinical score (0-39 range across 13 examination items) and MG-ADL score (0-24 range)
to measure treatment response for FcRn antagonists (Efgartigimod) and C5 complement inhibitors (Eculizumab).
"""

from typing import Dict


class MgQmgAdlScoreEngine:
    """Evaluates Quantitative Myasthenia Gravis (QMG) and MG-ADL activity scores."""

    def evaluate_mg_scores(
        self,
        qmg_total_score: int,  # 0 to 39
        mg_adl_total_score: int,  # 0 to 24
        achr_antibody_positive: bool = True,
        msk_antibody_positive: bool = False,
    ) -> Dict[str, any]:
        mg_severity = "MILD_MYASTHENIA"
        if mg_adl_total_score >= 10 or qmg_total_score >= 16:
            mg_severity = "SEVERE_MYASTHENIA"
        elif mg_adl_total_score >= 6 or qmg_total_score >= 10:
            mg_severity = "MODERATE_MYASTHENIA"

        targeted_biologic_indicated = mg_severity in ["MODERATE_MYASTHENIA", "SEVERE_MYASTHENIA"]

        biologic_agent = "EFGARTIGIMOD_FCRN_ANTAGONIST"
        if achr_antibody_positive and mg_severity == "SEVERE_MYASTHENIA":
            biologic_agent = "RAVULIZUMAB_C5_COMPLEMENT_INHIBITOR"
        elif msk_antibody_positive:
            biologic_agent = "RITUXIMAB_ANTI_CD20"

        recommendation = f"Myasthenia Gravis ({mg_severity}, MG-ADL {mg_adl_total_score}, QMG {qmg_total_score}): Maintain Pyridostigmine + oral prednisone/immunosuppressants"
        if targeted_biologic_indicated:
            recommendation = f"REACTION-GUIDED BIOLOGIC INDICATED ({mg_severity}, MG-ADL {mg_adl_total_score} >= 6): Initiate {biologic_agent} to induce rapid clinical response and decrease steroid burden"

        return {
            "qmg_total_score": qmg_total_score,
            "mg_adl_total_score": mg_adl_total_score,
            "mg_severity": mg_severity,
            "targeted_biologic_indicated": targeted_biologic_indicated,
            "recommended_biologic_agent": biologic_agent,
            "clinical_recommendation": recommendation,
            "status": "EVALUATION_COMPLETE",
        }


# Singleton engine instance
mg_score_engine = MgQmgAdlScoreEngine()
