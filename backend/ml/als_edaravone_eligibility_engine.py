"""
ALS Edaravone (Radicava) IV vs Oral Suspension Eligibility Engine
==================================================================
Evaluates FDA / Japan trial inclusion criteria for Edaravone (ALSFRS-R >= 2 on all items, %FVC >= 80%,
disease duration <= 2 years) to select IV infusion (60 mg/day) vs Oral suspension (105 mg/day).
"""

from typing import Dict


class AlsEdaravoneEligibilityEngine:
    """Evaluates Edaravone eligibility and formulation selection for ALS."""

    def evaluate_edaravone_eligibility(
        self,
        alsfrs_r_all_items_score_ge_2: bool = True,  # Score >= 2 on each of the 12 ALSFRS-R items
        percent_fvc: float = 85.0,  # >= 80% predicted
        disease_duration_years: float = 1.2,  # <= 2.0 years
        el_escorial_definite_or_probable_als: bool = True,
        preferred_formulation: str = "ORAL_SUSPENSION",  # ORAL_SUSPENSION or IV_INFUSION
    ) -> Dict[str, any]:
        strict_trial_eligible = (
            alsfrs_r_all_items_score_ge_2
            and percent_fvc >= 80.0
            and disease_duration_years <= 2.0
            and el_escorial_definite_or_probable_als
        )

        formulation = "RADICAVA_ORS_ORAL_SUSPENSION_105MG"
        if preferred_formulation == "IV_INFUSION":
            formulation = "RADICAVA_IV_INFUSION_60MG"

        recommendation = "Edaravone NOT indicated under strict trial criteria (Requires FVC >= 80%, duration <= 2 years, and ALSFRS-R scores >= 2); evaluate standard Riluzole therapy"
        if strict_trial_eligible:
            recommendation = f"ELIGIBLE FOR EDARAVONE (Radicava): Initiate {formulation} on 14-days-on / 14-days-off cycles (Initial cycle: 14 daily doses followed by 14 days off; subsequent cycles: 10 doses over 14 days followed by 14 days off)"

        return {
            "strict_trial_eligible": strict_trial_eligible,
            "recommended_formulation": formulation if strict_trial_eligible else "NONE",
            "cycle_schedule": "14_DAYS_ON_14_DAYS_OFF",
            "clinical_recommendation": recommendation,
            "status": "EVALUATION_COMPLETE",
        }


# Singleton engine instance
edaravone_engine = AlsEdaravoneEligibilityEngine()
