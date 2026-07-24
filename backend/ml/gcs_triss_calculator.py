"""
Glasgow Coma Scale (GCS) & TRISS Trauma Survival Calculator
============================================================
Computes GCS score (Eye + Verbal + Motor) and Trauma Injury Severity Score (TRISS) survival probability.
"""

from typing import Dict


class GcsTrissCalculator:
    """Calculates GCS and TRISS acute trauma survival probability."""

    def calculate_gcs_triss(
        self,
        eye_opening_score: int,  # 1 to 4
        verbal_response_score: int,  # 1 to 5
        motor_response_score: int,  # 1 to 6
        age_years: int,
        blunt_trauma: bool = True,
    ) -> Dict[str, any]:
        gcs_score = eye_opening_score + verbal_response_score + motor_response_score

        gcs_category = "MILD_HEAD_INJURY"
        if gcs_score <= 8:
            gcs_category = "SEVERE_HEAD_INJURY"
        elif gcs_score <= 12:
            gcs_category = "MODERATE_HEAD_INJURY"

        # Simplified TRISS probability calculation model
        base_survival = 98.0
        if gcs_score <= 8:
            base_survival -= (9 - gcs_score) * 8.0
        if age_years > 55:
            base_survival -= (age_years - 55) * 0.5

        estimated_survival_pct = round(max(base_survival, 5.0), 1)

        return {
            "gcs_total_score": gcs_score,
            "gcs_category": gcs_category,
            "estimated_survival_probability_percent": estimated_survival_pct,
            "airway_intubation_indicated": gcs_score <= 8,
            "status": "CALCULATION_COMPLETE",
        }


# Singleton calculator instance
gcs_triss_calculator = GcsTrissCalculator()
