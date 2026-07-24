"""
Asthma GINA Severity & Stepwise Pharmacotherapy Engine
======================================================
Evaluates GINA 2023 Track 1 (ICS-Formoterol reliever) vs Track 2 stepwise treatment (Steps 1 to 5)
based on symptom frequency, night awakenings, and FEV1.
"""

from typing import Dict


class AsthmaGinaTreatmentEngine:
    """Evaluates Asthma control and GINA 2023 stepwise management."""

    def evaluate_gina_treatment(
        self,
        daytime_symptoms_per_week: int,
        night_awakenings_per_month: int,
        fev1_percent_predicted: float,
        exacerbations_requiring_oral_steroids_past_year: int,
    ) -> Dict[str, any]:
        step = "STEP_1_2"
        regimen = "As-needed Low-Dose ICS-Formoterol (Track 1 Reliever & Controller)"

        if fev1_percent_predicted < 60.0 or exacerbations_requiring_oral_steroids_past_year >= 2 or daytime_symptoms_per_week >= 7:
            step = "STEP_4_5"
            regimen = "Medium/High-Dose ICS-Formoterol maintenance & reliever + consider Biologic add-on (Dupilumab / Omalizumab / Mepolizumab)"
        elif daytime_symptoms_per_week >= 4 or night_awakenings_per_month >= 4:
            step = "STEP_3"
            regimen = "Low-Dose ICS-Formoterol maintenance & reliever"

        uncontrolled = daytime_symptoms_per_week >= 4 or night_awakenings_per_month >= 2

        return {
            "gina_step_recommendation": step,
            "recommended_pharmacotherapy_track_1": regimen,
            "asthma_uncontrolled": uncontrolled,
            "biologic_eval_indicated": step == "STEP_4_5",
            "status": "EVALUATION_COMPLETE",
        }


# Singleton engine instance
asthma_gina_engine = AsthmaGinaTreatmentEngine()
