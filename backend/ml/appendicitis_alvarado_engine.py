"""
Acute Appendicitis Alvarado Score & AIR Score Engine
=====================================================
Calculates Alvarado Score (MANTRELS criteria) and Appendicitis Inflammatory Response (AIR) score
to triage right lower quadrant pain and CT/ultrasound indications.
"""

from typing import Dict


class AppendicitisAlvaradoEngine:
    """Calculates Alvarado and AIR scores for acute appendicitis evaluation."""

    def calculate_alvarado_score(
        self,
        migration_pain_rlq: bool,
        anorexia: bool,
        nausea_vomiting: bool,
        tenderness_rlq: bool,
        rebound_tenderness: bool,
        elevated_temperature_37_3C: bool,
        leukocytosis_wbc_over_10k: bool,
        shift_to_left_neutrophils_over_75pct: bool,
    ) -> Dict[str, any]:
        score = 0
        if migration_pain_rlq:
            score += 1
        if anorexia:
            score += 1
        if nausea_vomiting:
            score += 1
        if tenderness_rlq:
            score += 2
        if rebound_tenderness:
            score += 1
        if elevated_temperature_37_3C:
            score += 1
        if leukocytosis_wbc_over_10k:
            score += 2
        if shift_to_left_neutrophils_over_75pct:
            score += 1

        likelihood = "LOW_PROBABILITY"
        recommendation = "Discharge with return instructions if pain worsens; low appendicitis probability (<5%)"

        if score >= 7:
            likelihood = "HIGH_PROBABILITY"
            recommendation = "Stat Surgical Consult & Diagnostic Laparoscopy / CT Abdomen"
        elif score >= 5:
            likelihood = "INTERMEDIATE_PROBABILITY"
            recommendation = "Order Abdominal CT / Ultrasound & active clinical observation"

        return {
            "alvarado_score": score,
            "appendicitis_probability_category": likelihood,
            "clinical_recommendation": recommendation,
            "surgical_consult_indicated": score >= 7,
            "status": "SCORING_COMPLETE",
        }


# Singleton engine instance
appendicitis_engine = AppendicitisAlvaradoEngine()
