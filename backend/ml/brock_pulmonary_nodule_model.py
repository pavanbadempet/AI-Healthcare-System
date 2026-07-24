"""
Solitary Pulmonary Nodule Brock University Malignancy Predictor
================================================================
Computes 2-year cancer probability for solitary pulmonary nodules detected on screening CT scans.
"""

import math
from typing import Dict


class BrockPulmonaryNoduleModel:
    """Calculates Brock University (PanCan) risk model for pulmonary nodules."""

    def calculate_nodule_malignancy_probability(
        self,
        nodule_diameter_mm: float,
        female_sex: bool = False,
        spiculation_present: bool = False,
        upper_lobe_location: bool = False,
        part_solid_or_nonsolid: bool = False,
        family_history_lung_cancer: bool = False,
        emphysema_present: bool = False,
    ) -> Dict[str, any]:
        # Brock PanCan model log-odds
        log_odds = (
            -3.537
            + 0.1537 * nodule_diameter_mm
            + 0.6011 * (1 if female_sex else 0)
            + 0.7839 * (1 if spiculation_present else 0)
            + 0.6581 * (1 if upper_lobe_location else 0)
            + 0.2317 * (1 if part_solid_or_nonsolid else 0)
            + 0.4521 * (1 if family_history_lung_cancer else 0)
            + 0.2814 * (1 if emphysema_present else 0)
        )

        cancer_prob_pct = round((1.0 / (1.0 + math.exp(-log_odds))) * 100, 1)

        recommendation = "Low risk (<10%); repeat CT chest in 3-6 months per Fleischner guidelines"
        if cancer_prob_pct >= 65.0:
            recommendation = "High risk (>=65%); Surgical resection or VATS biopsy recommended"
        elif cancer_prob_pct >= 10.0:
            recommendation = "Intermediate risk (10-65%); Order PET-CT scan or tissue biopsy"

        return {
            "two_year_cancer_probability_percent": cancer_prob_pct,
            "risk_tier": "HIGH_RISK" if cancer_prob_pct >= 65.0 else ("INTERMEDIATE_RISK" if cancer_prob_pct >= 10.0 else "LOW_RISK"),
            "fleischner_guideline_recommendation": recommendation,
            "tissue_biopsy_or_resection_indicated": cancer_prob_pct >= 10.0,
            "status": "PREDICTION_COMPLETE",
        }


# Singleton model instance
brock_nodule_model = BrockPulmonaryNoduleModel()
