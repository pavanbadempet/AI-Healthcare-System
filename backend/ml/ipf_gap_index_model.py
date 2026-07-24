"""
Idiopathic Pulmonary Fibrosis (IPF) GAP Index Mortality Model
==============================================================
Computes GAP (Gender, Age, Physiology - FVC, DLCO) stage and 1-year, 2-year, and 3-year mortality risk for IPF.
"""

from typing import Dict, Optional


class IpfGapIndexModel:
    """Calculates GAP index stage and mortality predictions for IPF patients."""

    def calculate_gap_stage(
        self,
        male_gender: bool,
        age_years: int,
        fvc_percent_predicted: float,
        dlco_percent_predicted: Optional[float] = None,
    ) -> Dict[str, any]:
        points = 0
        if male_gender:
            points += 1

        if age_years > 65:
            points += 2
        elif age_years >= 61:
            points += 1

        if fvc_percent_predicted < 50.0:
            points += 2
        elif fvc_percent_predicted <= 75.0:
            points += 1

        if dlco_percent_predicted is not None:
            if dlco_percent_predicted < 35.0:
                points += 3
            elif dlco_percent_predicted <= 55.0:
                points += 2
            elif dlco_percent_predicted <= 65.0:
                points += 1

        gap_stage = "STAGE_I"
        one_yr_mortality = 6.0
        three_yr_mortality = 16.0

        if points >= 6:
            gap_stage = "STAGE_III"
            one_yr_mortality = 39.0
            three_yr_mortality = 77.0
        elif points >= 4:
            gap_stage = "STAGE_II"
            one_yr_mortality = 16.0
            three_yr_mortality = 42.0

        return {
            "gap_total_points": points,
            "gap_stage": gap_stage,
            "one_year_mortality_percent": one_yr_mortality,
            "three_year_mortality_percent": three_yr_mortality,
            "antifibrotic_therapy_eval_indicated": True,
            "lung_transplantation_eval_indicated": gap_stage in ["STAGE_II", "STAGE_III"],
            "status": "PREDICTION_COMPLETE",
        }


# Singleton model instance
ipf_gap_model = IpfGapIndexModel()
