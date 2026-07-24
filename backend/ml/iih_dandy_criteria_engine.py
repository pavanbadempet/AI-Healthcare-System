"""
Idiopathic Intracranial Hypertension (IIH) Dandy Criteria Evaluator
====================================================================
Evaluates Modified Dandy Criteria (LP opening pressure > 25 cm H2O, normal CSF, papilledema,
and normal MRI/MRV venous sinus imaging) for IIH diagnosis.
"""

from typing import Dict


class IihDandyCriteriaEngine:
    """Evaluates Modified Dandy Criteria for Idiopathic Intracranial Hypertension (Pseudotumor Cerebri)."""

    def evaluate_iih_dandy_criteria(
        self,
        lumbar_puncture_opening_pressure_cm_h2o: float,
        normal_csf_composition_and_cytology: bool,
        papilledema_present_on_fundoscopy: bool,
        normal_mri_brain_no_mass_lesion: bool,
        mrv_venous_sinus_thrombosis_excluded: bool,
    ) -> Dict[str, any]:
        dandy_criteria_met = (
            lumbar_puncture_opening_pressure_cm_h2o > 25.0
            and normal_csf_composition_and_cytology
            and papilledema_present_on_fundoscopy
            and normal_mri_brain_no_mass_lesion
            and mrv_venous_sinus_thrombosis_excluded
        )

        diagnosis = "IDIOPATHIC_INTRACRANIAL_HYPERTENSION" if dandy_criteria_met else "OTHER_INTRACRANIAL_PATHOLOGY"

        recommendation = "Criteria not fully met; investigate venous sinus thrombosis, intracranial mass, or meningeal infection"
        if dandy_criteria_met:
            recommendation = "Modified Dandy Criteria Met: Initiate Acetazolamide 500mg BID, weight loss program, & serial automated visual field testing"

        return {
            "lp_opening_pressure_cm_h2o": lumbar_puncture_opening_pressure_cm_h2o,
            "modified_dandy_criteria_met": dandy_criteria_met,
            "iih_diagnosis": diagnosis,
            "acetazolamide_and_weight_loss_indicated": dandy_criteria_met,
            "clinical_recommendation": recommendation,
            "status": "EVALUATION_COMPLETE",
        }


# Singleton engine instance
iih_dandy_engine = IihDandyCriteriaEngine()
