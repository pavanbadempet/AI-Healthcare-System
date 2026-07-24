"""
CHADS2-VASc Atrial Fibrillation Stroke Risk Calculator
======================================================
Calculates annual stroke risk percentage for non-valvular atrial fibrillation patients
and guides oral anticoagulation recommendations (Apixaban/Rivaroxaban vs Aspirin vs None).
"""

from typing import Dict


class Chads2VascCalculator:
    """Calculates CHA2DS2-VASc score and anticoagulation recommendations."""

    def calculate_chads_vasc_score(
        self,
        congestive_heart_failure: bool,
        hypertension: bool,
        age_years: int,
        diabetes_mellitus: bool,
        prior_stroke_tia_thromboembolism: bool,
        vascular_disease: bool,
        female_sex: bool,
    ) -> Dict[str, any]:
        score = 0
        if congestive_heart_failure:
            score += 1
        if hypertension:
            score += 1
        if age_years >= 75:
            score += 2
        elif age_years >= 65:
            score += 1

        if diabetes_mellitus:
            score += 1
        if prior_stroke_tia_thromboembolism:
            score += 2
        if vascular_disease:
            score += 1
        if female_sex:
            score += 1

        stroke_risk_map = {0: 0.2, 1: 0.6, 2: 2.2, 3: 3.2, 4: 4.8, 5: 7.2, 6: 9.7, 7: 11.2, 8: 12.5, 9: 15.2}
        annual_stroke_risk_pct = stroke_risk_map.get(min(score, 9), 15.2)

        anticoagulation_recommendation = "No antithrombotic therapy required"
        if (female_sex and score >= 2) or (not female_sex and score >= 1):
            anticoagulation_recommendation = "Oral Anticoagulation strongly recommended (DOAC preferred: Apixaban / Rivaroxaban / Dabigatran)"
        elif (not female_sex and score == 1) or (female_sex and score == 2):
            anticoagulation_recommendation = "Consider Oral Anticoagulation or Aspirin based on clinical risk discussion"

        return {
            "chads_vasc_score": score,
            "annual_ischemic_stroke_risk_percent": annual_stroke_risk_pct,
            "anticoagulation_recommendation": anticoagulation_recommendation,
            "oral_anticoagulation_indicated": "strongly recommended" in anticoagulation_recommendation.lower(),
            "status": "SCORING_COMPLETE",
        }


# Singleton calculator instance
chads_vasc_calculator = Chads2VascCalculator()
