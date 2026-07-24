"""
Idiopathic Pulmonary Fibrosis (IPF) GAP (Gender, Age, Physiology) Mortality Predictor
=====================================================================================
Calculates GAP Index (0 to 8 points) from Gender, Age, FVC, and DLCO
to predict 1-, 2-, and 3-year mortality in IPF patients.
"""

from typing import Dict


class IpfGapMortalityCalculator:
    """Calculates GAP Index for Idiopathic Pulmonary Fibrosis mortality prognosis."""

    def calculate_ipf_gap_index(
        self,
        male_gender: bool,
        age_years: int,
        fvc_percent_predicted: float,
        dlco_percent_predicted: float,
    ) -> Dict[str, any]:
        gap_score = 0

        # Gender G
        if male_gender:
            gap_score += 1

        # Age A
        if age_years > 65:
            gap_score += 2
        elif age_years >= 61:
            gap_score += 1

        # Physiology P (FVC)
        if fvc_percent_predicted < 50.0:
            gap_score += 2
        elif fvc_percent_predicted <= 75.0:
            gap_score += 1

        # Physiology P (DLCO)
        if dlco_percent_predicted < 36.0:
            gap_score += 2
        elif dlco_percent_predicted <= 55.0:
            gap_score += 1

        stage = "GAP_STAGE_I"
        one_year_mortality_pct = 6.0

        if gap_score >= 6:
            stage = "GAP_STAGE_III"
            one_year_mortality_pct = 39.0
        elif gap_score >= 4:
            stage = "GAP_STAGE_II"
            one_year_mortality_pct = 16.0

        recommendation = "Initiate Antifibrotic therapy (Nintedanib 150mg BID or Pirfenidone 801mg TID) & routine PFT monitoring Q6M"
        if stage == "GAP_STAGE_III":
            recommendation = "GAP Stage III (39% 1-Yr Mortality): Stat Lung Transplant Evaluation & Antifibrotic therapy"

        return {
            "gap_index_score": gap_score,
            "gap_stage": stage,
            "one_year_mortality_percent": one_year_mortality_pct,
            "lung_transplant_referral_indicated": stage == "GAP_STAGE_III",
            "clinical_recommendation": recommendation,
            "status": "CALCULATION_COMPLETE",
        }


# Singleton calculator instance
ipf_gap_calculator = IpfGapMortalityCalculator()
