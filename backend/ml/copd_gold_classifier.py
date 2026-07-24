"""
COPD GOLD Staging & Exacerbation Risk Classifier
=================================================
Classifies COPD patients into GOLD Groups A, B, E (2023 update) based on spirometry grade (GOLD 1-4),
mMRC dyspnea score, CAT score, and 12-month exacerbation history.
"""

from typing import Dict


class CopdGoldClassifier:
    """Classifies COPD severity and GOLD 2023 treatment group."""

    def classify_copd(
        self,
        fev1_percent_predicted: float,
        mmrc_dyspnea_score: int,  # 0 to 4
        cat_assessment_score: int,  # 0 to 40
        exacerbations_past_12m: int,
        hospitalizations_past_12m: int,
    ) -> Dict[str, any]:
        # Spirometry Grade (GOLD 1 to 4)
        gold_grade = "GOLD_1_MILD"
        if fev1_percent_predicted < 30.0:
            gold_grade = "GOLD_4_VERY_SEVERE"
        elif fev1_percent_predicted < 50.0:
            gold_grade = "GOLD_3_SEVERE"
        elif fev1_percent_predicted < 80.0:
            gold_grade = "GOLD_2_MODERATE"

        # GOLD 2023 Group (A, B, E)
        high_exacerbation_risk = exacerbations_past_12m >= 2 or hospitalizations_past_12m >= 1
        high_symptom_burden = mmrc_dyspnea_score >= 2 or cat_assessment_score >= 10

        gold_group = "GROUP_A"
        initial_pharmacotherapy = "Bronchodilator (LAMA or LABA)"

        if high_exacerbation_risk:
            gold_group = "GROUP_E"
            initial_pharmacotherapy = "Dual Bronchodilator (LABA + LAMA); add ICS if Blood Eosinophils >= 300"
        elif high_symptom_burden:
            gold_group = "GROUP_B"
            initial_pharmacotherapy = "Dual Bronchodilator (LABA + LAMA)"

        return {
            "fev1_percent_predicted": fev1_percent_predicted,
            "spirometry_gold_grade": gold_grade,
            "gold_2023_group": gold_group,
            "initial_pharmacotherapy_recommendation": initial_pharmacotherapy,
            "high_exacerbation_risk": high_exacerbation_risk,
            "status": "CLASSIFICATION_COMPLETE",
        }


# Singleton classifier instance
copd_gold_classifier = CopdGoldClassifier()
