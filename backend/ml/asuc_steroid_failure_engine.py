"""
Acute Severe Ulcerative Colitis (ASUC) Day 3 Steroid Failure & Rescue Therapy Engine
=====================================================================================
Evaluates Travis Criteria (stool frequency > 8/day OR 3-8 stools/day + CRP > 45 mg/L on Day 3 of IV hydrocortisone)
and Oxford criteria predicting 85% colectomy risk to initiate rescue biological therapy (Infliximab 10 mg/kg or Tofacitinib 10 mg BID).
"""

from typing import Dict


class AsucSteroidFailureEngine:
    """Evaluates Day 3 IV steroid failure in ASUC and guides biological rescue therapy vs colectomy."""

    def evaluate_day3_steroid_response(
        self,
        days_on_iv_hydrocortisone: int,  # Day 3 evaluation standard
        bloody_stool_frequency_per_day: int,  # Travis: > 8 or 3-8
        crp_mg_L: float,  # Travis: CRP > 45 mg/L
        tachycardic_hr_bpm: float = 85.0,
        hemoglobin_g_dL: float = 11.5,
    ) -> Dict[str, any]:
        travis_failure = (
            days_on_iv_hydrocortisone >= 3
            and (bloody_stool_frequency_per_day > 8 or (bloody_stool_frequency_per_day >= 3 and crp_mg_L > 45.0))
        )

        oxford_high_colectomy_risk = travis_failure

        recommendation = "STEROID RESPONSE ADEQUATE: Continue IV Hydrocortisone 100 mg q6h for up to 5 days, then transition to oral Prednisolone 40 mg daily taper."
        if travis_failure:
            recommendation = f"DAY 3 STEROID FAILURE IDENTIFIED (Travis Criteria met: Stool freq {bloody_stool_frequency_per_day}/day, CRP {crp_mg_L} mg/L - 85% Colectomy Risk): MANDATE immediate Rescue Therapy with accelerated Infliximab (10 mg/kg at Day 0, Day 7, Day 14) or oral Tofacitinib (10 mg BID). Obtain emergency colorectal surgery consultation."

        return {
            "days_on_iv_steroids": days_on_iv_hydrocortisone,
            "travis_criteria_failed": travis_failure,
            "oxford_colectomy_risk_pct": 85.0 if oxford_high_colectomy_risk else 15.0,
            "rescue_therapy_indicated": travis_failure,
            "clinical_recommendation": recommendation,
            "status": "EVALUATION_COMPLETE",
        }


# Singleton engine instance
asuc_steroid_failure_engine = AsucSteroidFailureEngine()
