"""
Renal Artery Stenosis Risk & Renovascular Hypertension Engine
==============================================================
Evaluates refractory hypertension, ACEi/ARB-induced creatinine rise (>30%),
and renal duplex ultrasound peak systolic velocity (PSV > 180 cm/s) to flag renovascular hypertension.
"""

from typing import Dict


class RenalArteryStenosisEngine:
    """Evaluates clinical risk criteria for Renal Artery Stenosis (RAS)."""

    def evaluate_ras_risk(
        self,
        refractory_hypertension_3_or_more_meds: bool,
        creatinine_rise_over_30pct_after_acei_arb: bool,
        abdominal_bruit_present: bool = False,
        duplex_psv_cm_s: float = 120.0,
        unexplained_asymmetric_kidney_size: bool = False,
    ) -> Dict[str, any]:
        risk_score = 0
        if refractory_hypertension_3_or_more_meds:
            risk_score += 1
        if creatinine_rise_over_30pct_after_acei_arb:
            risk_score += 2
        if abdominal_bruit_present:
            risk_score += 2
        if duplex_psv_cm_s > 180.0:
            risk_score += 3
        if unexplained_asymmetric_kidney_size:
            risk_score += 1

        high_probability = risk_score >= 3 or duplex_psv_cm_s > 180.0

        recommendation = "Low suspicion for RAS; maintain blood pressure control"
        if high_probability:
            recommendation = "Order Renal MR Angiography (MRA) or CT Angiography (CTA) & Vascular Surgery consult for potential angioplasty/stenting"

        return {
            "ras_risk_score": risk_score,
            "high_probability_ras": high_probability,
            "renovascular_hypertension_suspected": high_probability,
            "diagnostic_imaging_recommendation": recommendation,
            "status": "EVALUATION_COMPLETE",
        }


# Singleton engine instance
ras_engine = RenalArteryStenosisEngine()
