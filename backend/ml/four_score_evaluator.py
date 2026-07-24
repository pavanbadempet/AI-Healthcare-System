"""
Four-Score Neurological Coma Scale Evaluator
=============================================
Computes FOUR (Full Outline of UnResponsiveNess) Score (Eye, Motor, Brainstem, Respiration) for ICU neuro-prognostication.
"""

from typing import Dict


class FourScoreEvaluator:
    """Calculates FOUR score for ICU coma depth and brainstem reflex monitoring."""

    def calculate_four_score(
        self,
        eye_response_score: int,  # 0 to 4
        motor_response_score: int,  # 0 to 4
        brainstem_reflexes_score: int,  # 0 to 4
        respiration_pattern_score: int,  # 0 to 4
    ) -> Dict[str, any]:
        total_score = eye_response_score + motor_response_score + brainstem_reflexes_score + respiration_pattern_score

        category = "MILD_IMPAIRMENT"
        mortality_risk_tier = "LOW"
        if total_score <= 4:
            category = "SEVERE_COMA_BRAINSTEM_REFLEX_DEFICIT"
            mortality_risk_tier = "EXTREMELY_HIGH"
        elif total_score <= 8:
            category = "MODERATE_TO_SEVERE_COMA"
            mortality_risk_tier = "HIGH"
        elif total_score <= 12:
            category = "MODERATE_COMA"
            mortality_risk_tier = "MODERATE"

        brainstem_intact = brainstem_reflexes_score >= 3

        return {
            "four_total_score": total_score,
            "neurological_category": category,
            "mortality_risk_tier": mortality_risk_tier,
            "brainstem_reflexes_intact": brainstem_intact,
            "status": "SCORING_COMPLETE",
        }


# Singleton evaluator instance
four_score_evaluator = FourScoreEvaluator()
