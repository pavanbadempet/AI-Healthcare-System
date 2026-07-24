"""
Amyotrophic Lateral Sclerosis ALSFRS-R Progression Engine
==========================================================
Scores Revised ALS Functional Rating Scale (0 to 48 points across 12 domains)
and calculates progression slope (delta ALSFRS-R/month) to guide NIV and PEG referrals.
"""

from typing import Dict, Optional


class AlsFrsRCalculator:
    """Calculates ALSFRS-R score and progression rate for ALS motor neuron disease."""

    def calculate_alsfrs_r_score(
        self,
        speech_0_to_4: int,
        salivation_0_to_4: int,
        swallowing_0_to_4: int,
        handwriting_0_to_4: int,
        cutting_food_0_to_4: int,
        dressing_hygiene_0_to_4: int,
        turning_in_bed_0_to_4: int,
        walking_0_to_4: int,
        climbing_stairs_0_to_4: int,
        dyspnea_0_to_4: int,
        orthopnea_0_to_4: int,
        respiratory_insufficiency_0_to_4: int,
        disease_duration_months: Optional[float] = None,
    ) -> Dict[str, any]:
        total_score = (
            speech_0_to_4
            + salivation_0_to_4
            + swallowing_0_to_4
            + handwriting_0_to_4
            + cutting_food_0_to_4
            + dressing_hygiene_0_to_4
            + turning_in_bed_0_to_4
            + walking_0_to_4
            + climbing_stairs_0_to_4
            + dyspnea_0_to_4
            + orthopnea_0_to_4
            + respiratory_insufficiency_0_to_4
        )

        bulbar_subscore = speech_0_to_4 + salivation_0_to_4 + swallowing_0_to_4
        respiratory_subscore = dyspnea_0_to_4 + orthopnea_0_to_4 + respiratory_insufficiency_0_to_4

        progression_rate_pts_per_month = None
        if disease_duration_months is not None and disease_duration_months > 0:
            progression_rate_pts_per_month = round((48.0 - total_score) / disease_duration_months, 2)

        niv_non_invasive_ventilation_indicated = respiratory_subscore <= 8 or orthopnea_0_to_4 <= 2
        peg_feeding_tube_indicated = swallowing_0_to_4 <= 2

        recommendation = "ALSFRS-R monitored: Maintain Riluzole (50 mg BID) & multidisciplinary ALS clinic follow-up"
        if niv_non_invasive_ventilation_indicated and peg_feeding_tube_indicated:
            recommendation = "Severe Bulbar & Respiratory ALS Decline: Urgently initiate Non-Invasive Ventilation (BiPAP/NIV) & Gastroenterology consult for Percutaneous Endoscopic Gastrostomy (PEG)"
        elif niv_non_invasive_ventilation_indicated:
            recommendation = "Respiratory Insufficiency (Respiratory Subscore <= 8): Initiate BiPAP/NIV nocturnal ventilation & Pulmonology consult"
        elif peg_feeding_tube_indicated:
            recommendation = "Dysphagia / Bulbar Decline (Swallowing <= 2): Evaluate for PEG tube insertion to prevent aspiration & weight loss"

        return {
            "total_alsfrs_r_score": total_score,
            "bulbar_subscore": bulbar_subscore,
            "respiratory_subscore": respiratory_subscore,
            "progression_rate_pts_per_month": progression_rate_pts_per_month,
            "non_invasive_ventilation_niv_indicated": niv_non_invasive_ventilation_indicated,
            "peg_gastrostomy_tube_indicated": peg_feeding_tube_indicated,
            "clinical_recommendation": recommendation,
            "status": "CALCULATION_COMPLETE",
        }


# Singleton engine instance
alsfrs_r_calculator = AlsFrsRCalculator()
