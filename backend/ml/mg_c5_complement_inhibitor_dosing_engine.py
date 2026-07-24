"""
Myasthenia Gravis Complement C5 Inhibitor (Eculizumab vs Ravulizumab) Engine
=============================================================================
Evaluates refractory AChR+ gMG: verifies Meningococcal vaccination (ACWY + MenB >= 2 weeks prior)
and calculates Ravulizumab (3000 mg load -> 3300 mg Q8W) vs Eculizumab (900 mg QW -> 1200 mg Q2W) dosing.
"""

from typing import Dict


class MgC5ComplementInhibitorDosingEngine:
    """Evaluates C5 complement inhibitor selection and meningococcal safety rules in gMG."""

    def evaluate_c5_inhibitor_dosing(
        self,
        achr_antibody_positive: bool = True,
        meningococcal_vaccination_acwy_and_menb_received: bool = True,
        weeks_since_vaccination: float = 3.0,  # >= 2 weeks required
        patient_weight_kg: float = 75.0,
        preferred_agent: str = "RAVULIZUMAB",  # RAVULIZUMAB or ECULIZUMAB
    ) -> Dict[str, any]:
        vaccine_safe = (
            meningococcal_vaccination_acwy_and_menb_received and weeks_since_vaccination >= 2.0
        )

        eligible = achr_antibody_positive and vaccine_safe

        loading_dose = "3000 mg IV"
        maintenance_dose = "3300 mg IV every 8 weeks"

        if preferred_agent == "ECULIZUMAB":
            loading_dose = "900 mg IV weekly for 4 weeks"
            maintenance_dose = "1200 mg IV every 2 weeks"

        recommendation = "C5 Inhibitor CONTRAINDICATED / HOLD: Requires Neisseria Meningitidis ACWY & MenB vaccination >= 2 weeks prior to first dose (or prophylactic oral Penicillin V / Ciprofloxacin until 2 weeks post-vaccine)"
        if eligible:
            recommendation = f"ELIGIBLE FOR {preferred_agent} (C5 Complement Inhibitor): Administer {preferred_agent} loading ({loading_dose}) followed by maintenance ({maintenance_dose}). Provide patient safety card for meningococcal infection awareness"

        return {
            "eligible_for_c5_inhibitor": eligible,
            "meningococcal_vaccine_verified": vaccine_safe,
            "selected_c5_agent": preferred_agent if eligible else "NONE",
            "loading_dose_regimen": loading_dose if eligible else "NONE",
            "maintenance_dose_regimen": maintenance_dose if eligible else "NONE",
            "clinical_recommendation": recommendation,
            "status": "EVALUATION_COMPLETE",
        }


# Singleton engine instance
c5_inhibitor_engine = MgC5ComplementInhibitorDosingEngine()
