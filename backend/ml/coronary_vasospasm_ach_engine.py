"""
Invasive Coronary Vasospasm Acetylcholine (ACh) Provocation Engine
==================================================================
Evaluates intracoronary Acetylcholine (ACh) provocation testing
to diagnose Vasospastic (Prinzmetal) Angina and microvascular spasm.
"""

from typing import Dict


class CoronaryVasospasmAchEngine:
    """Evaluates intracoronary ACh reactivity testing for vasospastic angina."""

    def evaluate_ach_provocation_test(
        self,
        max_epicardial_diameter_reduction_percent: float,
        ischemic_st_shift_present: bool,
        typical_anginal_chest_pain_reproduced: bool,
        ach_dose_micrograms: float = 100.0,
        microvascular_spasm_suspected: bool = False,
    ) -> Dict[str, any]:
        epicardial_vasospasm = (
            max_epicardial_diameter_reduction_percent >= 90.0
            and ischemic_st_shift_present
            and typical_anginal_chest_pain_reproduced
        )

        diagnosis = "NEGATIVE_ACH_PROVOCATION_TEST"
        calcium_channel_blockers_indicated = False

        if epicardial_vasospasm:
            diagnosis = "EPICARDIAL_VASOSPASTIC_PRINZMETAL_ANGINA"
            calcium_channel_blockers_indicated = True
        elif microvascular_spasm_suspected or (ischemic_st_shift_present and typical_anginal_chest_pain_reproduced):
            diagnosis = "CORONARY_MICROVASCULAR_SPASM"
            calcium_channel_blockers_indicated = True

        recommendation = "Negative ACh Test: Avoid unnecessary nitrates; investigate non-ischemic causes"
        if calcium_channel_blockers_indicated:
            recommendation = "Positive ACh Test: Initiate High-Dose Calcium Channel Blockers (Diltiazem 240-360mg / Verapamil) + Sublingual Nitroglycerin; strictly avoid Non-selective Beta-Blockers"

        return {
            "max_epicardial_diameter_reduction_percent": max_epicardial_diameter_reduction_percent,
            "epicardial_vasospasm_confirmed": epicardial_vasospasm,
            "vasospastic_angina_diagnosis": diagnosis,
            "calcium_channel_blocker_therapy_indicated": calcium_channel_blockers_indicated,
            "avoid_beta_blockers": calcium_channel_blockers_indicated,
            "clinical_recommendation": recommendation,
            "status": "EVALUATION_COMPLETE",
        }


# Singleton engine instance
ach_vasospasm_engine = CoronaryVasospasmAchEngine()
