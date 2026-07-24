"""
Guillain-Barré Syndrome mEGRIS (Modified Erasmus GBS Respiratory Insufficiency Score) Engine
===========================================================================================
Calculates mEGRIS score (0 to 7 points) on admission to predict mechanical ventilation risk within 1 week.
"""

from typing import Dict


class MegrisGbsRespiratoryEngine:
    """Calculates mEGRIS score for Guillain-Barré Syndrome respiratory insufficiency prediction."""

    def calculate_megris_score(
        self,
        days_between_onset_and_admission: int,  # <=3d (2), 4-7d (1), >7d (0)
        facial_or_bulbar_weakness_present: bool,  # Yes (1), No (0)
        mrc_sum_score_0_to_60: int,              # <31 (4), 31-40 (3), 41-50 (2), 51-60 (0)
    ) -> Dict[str, any]:
        score = 0

        # Days from onset
        if days_between_onset_and_admission <= 3:
            score += 2
        elif days_between_onset_and_admission <= 7:
            score += 1

        # Facial/bulbar weakness
        if facial_or_bulbar_weakness_present:
            score += 1

        # MRC sum score
        if mrc_sum_score_0_to_60 < 31:
            score += 4
        elif mrc_sum_score_0_to_60 <= 40:
            score += 3
        elif mrc_sum_score_0_to_60 <= 50:
            score += 2

        ventilation_risk_pct = 4.0
        if score >= 5:
            ventilation_risk_pct = 65.0
        elif score >= 3:
            ventilation_risk_pct = 24.0

        icu_intubation_prep = score >= 5

        recommendation = "Low mEGRIS score (<3): Monitor vital capacity (FVC Q4H) on neurology ward"
        if icu_intubation_prep:
            recommendation = "High mEGRIS score (>=5; 65% Ventilation Risk): Stat Neuro-ICU Transfer, IVIG (2g/kg over 5d) / PLEX, & elective intubation protocol if FVC < 20 mL/kg"

        return {
            "megris_total_score": score,
            "one_week_mechanical_ventilation_risk_percent": ventilation_risk_pct,
            "stat_neuro_icu_and_intubation_prep_indicated": icu_intubation_prep,
            "clinical_recommendation": recommendation,
            "status": "SCORING_COMPLETE",
        }


# Singleton engine instance
megris_gbs_engine = MegrisGbsRespiratoryEngine()
