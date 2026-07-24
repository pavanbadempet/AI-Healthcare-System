"""
HAS-BLED Major Bleeding Risk Calculator for AFib
=================================================
Computes annual major bleeding risk score for patients on anticoagulation
(Hypertension, Abnormal renal/liver, Stroke, Bleeding history, Labile INR, Elderly, Drugs/alcohol).
"""

from typing import Dict


class HasBledCalculator:
    """Calculates HAS-BLED score for anticoagulation bleeding risk assessment."""

    def calculate_has_bled_score(
        self,
        uncontrolled_hypertension: bool,
        abnormal_renal_function: bool,
        abnormal_liver_function: bool,
        prior_stroke_history: bool,
        prior_major_bleeding_history: bool,
        labile_inr: bool,
        age_over_65: bool,
        concomitant_antiplatelet_nsaid: bool,
        alcohol_use_excess: bool,
    ) -> Dict[str, any]:
        score = 0
        if uncontrolled_hypertension:
            score += 1
        if abnormal_renal_function:
            score += 1
        if abnormal_liver_function:
            score += 1
        if prior_stroke_history:
            score += 1
        if prior_major_bleeding_history:
            score += 1
        if labile_inr:
            score += 1
        if age_over_65:
            score += 1
        if concomitant_antiplatelet_nsaid:
            score += 1
        if alcohol_use_excess:
            score += 1

        bleeding_risk_map = {0: 1.1, 1: 1.0, 2: 1.9, 3: 3.7, 4: 8.7, 5: 12.5}
        annual_bleeding_risk_pct = bleeding_risk_map.get(min(score, 5), 12.5)

        high_risk = score >= 3

        return {
            "has_bled_score": score,
            "annual_major_bleeding_risk_percent": annual_bleeding_risk_pct,
            "high_bleeding_risk": high_risk,
            "clinical_recommendation": "Address modifiable bleeding risk factors & schedule frequent clinical follow-up" if high_risk else "Standard anticoagulation monitoring",
            "status": "SCORING_COMPLETE",
        }


# Singleton calculator instance
has_bled_calculator = HasBledCalculator()
