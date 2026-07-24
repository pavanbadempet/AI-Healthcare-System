"""
Left Ventricular Non-Compaction (LVNC) Jenni Echo Criteria Classifier
======================================================================
Calculates non-compacted to compacted myocardium ratio (NC/C > 2.0 at end-systole)
and color Doppler inter-trabecular recess flow to diagnose LVNC.
"""

from typing import Dict


class LvncJenniCriteriaEngine:
    """Classifies Left Ventricular Non-Compaction cardiomyopathy via Jenni Echocardiographic criteria."""

    def evaluate_lvnc_jenni_criteria(
        self,
        nc_c_ratio_end_systole: float,
        intertrabecular_recess_flow_color_doppler: bool,
        two_layer_myocardial_structure_present: bool,
        prominent_trabeculations_apical_lateral: bool,
    ) -> Dict[str, any]:
        jenni_criteria_met = (
            nc_c_ratio_end_systole > 2.0
            and intertrabecular_recess_flow_color_doppler
            and two_layer_myocardial_structure_present
            and prominent_trabeculations_apical_lateral
        )

        diagnosis = "LVNC_LEFT_VENTRICULAR_NON_COMPACTION" if jenni_criteria_met else "NORMAL_OR_OTHER_CARDIOMYOPATHY"

        recommendation = "Criteria not fully met; maintain standard cardiac surveillance"
        if jenni_criteria_met:
            recommendation = "Jenni Echocardiographic Criteria Met: Confirm with Cardiac MRI (Petersen ratio > 2.3), initiate anticoagulation if EF < 40%, & perform family genetic screening"

        return {
            "nc_c_ratio_end_systole": nc_c_ratio_end_systole,
            "jenni_criteria_met": jenni_criteria_met,
            "lvnc_diagnosis": diagnosis,
            "cardiac_mri_and_anticoagulation_indicated": jenni_criteria_met,
            "clinical_recommendation": recommendation,
            "status": "EVALUATION_COMPLETE",
        }


# Singleton engine instance
lvnc_jenni_engine = LvncJenniCriteriaEngine()
