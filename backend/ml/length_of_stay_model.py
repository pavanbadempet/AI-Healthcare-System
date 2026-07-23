"""
Hospital Length of Stay (LOS) Predictor ML Model
=================================================
Predicts inpatient length of stay (days) and discharge readiness scores based on
admission acuity, age, Charlson comorbidity index, and initial vital sign stability.
"""

from typing import Dict, Optional


class LengthOfStayModel:
    """Predicts hospital inpatient length of stay in days."""

    def predict_length_of_stay(
        self,
        age: int,
        is_icu_admission: bool,
        charlson_comorbidity_index: int,
        admission_systolic_bp: float = 120.0,
    ) -> Dict[str, any]:
        base_los = 3.0

        if is_icu_admission:
            base_los += 4.5

        if age >= 70:
            base_los += 1.5

        base_los += charlson_comorbidity_index * 0.8

        if admission_systolic_bp > 180 or admission_systolic_bp < 90:
            base_los += 1.2

        predicted_days = round(base_los, 1)

        return {
            "predicted_los_days": predicted_days,
            "complexity_tier": "HIGH" if predicted_days >= 7.0 else ("MODERATE" if predicted_days >= 4.0 else "LOW"),
            "discharge_planning_flag": predicted_days >= 6.0,
        }


# Singleton model instance
los_model = LengthOfStayModel()
