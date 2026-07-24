"""
Atrial Fibrillation HAS-BLED vs CHA2DS2-VASc Benefit-Risk Evaluator
====================================================================
Calculates net clinical benefit score (stroke prevention vs major bleeding risk)
for oral anticoagulation decisions in non-valvular atrial fibrillation.
"""

from typing import Dict


class AfibNetBenefitEvaluator:
    """Evaluates net clinical benefit of anticoagulation in AFib."""

    def evaluate_net_benefit(
        self,
        stroke_risk_annual_pct: float,
        bleeding_risk_annual_pct: float,
        patient_age_years: int,
    ) -> Dict[str, any]:
        # Net clinical benefit calculation (Stroke risk - 1.5 * Bleeding risk)
        net_benefit = round(stroke_risk_annual_pct - (1.5 * bleeding_risk_annual_pct), 2)

        favorable_for_oac = net_benefit > 0.0 or stroke_risk_annual_pct >= 2.2

        return {
            "annual_stroke_risk_percent": stroke_risk_annual_pct,
            "annual_bleeding_risk_percent": bleeding_risk_annual_pct,
            "net_clinical_benefit_score": net_benefit,
            "anticoagulation_net_favorable": favorable_for_oac,
            "clinical_decision_recommendation": "Net clinical benefit favors DOAC anticoagulation" if favorable_for_oac else "High bleeding risk relative to stroke risk; shared decision-making required",
            "status": "EVALUATION_COMPLETE",
        }


# Singleton evaluator instance
afib_net_benefit_evaluator = AfibNetBenefitEvaluator()
