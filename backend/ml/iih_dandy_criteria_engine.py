"""
Idiopathic Intracranial Hypertension (IIH) Dandy Criteria & Papilledema Engine
==============================================================================
Evaluates Modified Dandy Criteria: Lumbar puncture opening pressure (>= 250 mm H2O),
Frisén Papilledema Grade (0-5), MRV transverse sinus stenosis, and visual field MD (dB)
to guide Acetazolamide (1000-4000 mg/day) vs Venous Sinus Stenting vs ONSF surgery.
"""

from typing import Dict


class IihDandyCriteriaEngine:
    """Evaluates Idiopathic Intracranial Hypertension (IIH) Dandy criteria and papilledema."""

    def evaluate_iih_dandy_criteria(
        self,
        lp_opening_pressure_mm_h2o: float,
        frisen_papilledema_grade: int,  # 0 to 5
        visual_field_mean_deviation_db: float,  # e.g., -2.0 to -15.0 dB
        csf_composition_normal: bool = True,
        mri_mrv_no_mass_or_venous_thrombosis: bool = True,
        transverse_sinus_stenosis_present: bool = False,
        adult_patient: bool = True,
    ) -> Dict[str, any]:
        pressure_cutoff = 250.0 if adult_patient else 280.0
        elevated_icp = lp_opening_pressure_mm_h2o >= pressure_cutoff

        dandy_criteria_met = elevated_icp and csf_composition_normal and mri_mrv_no_mass_or_venous_thrombosis

        fulminant_iih = frisen_papilledema_grade >= 4 or visual_field_mean_deviation_db <= -7.0

        recommended_treatment = "WEIGHT_LOSS_AND_CONSERVATIVE_MONITORING"
        if dandy_criteria_met:
            if fulminant_iih:
                if transverse_sinus_stenosis_present:
                    recommended_treatment = "TRANSVERSE_SINUS_STENTING_OR_OPTIC_NERVE_SHEATH_FENESTRATION"
                else:
                    recommended_treatment = "EMERGENT_OPTIC_NERVE_SHEATH_FENESTRATION_ONSF_OR_VP_SHUNT"
            else:
                recommended_treatment = "HIGH_DOSE_ACETAZOLAMIDE_1000_TO_4000MG_DAILY_AND_WEIGHT_MANAGEMENT"

        recommendation = "Criteria for IIH not met; investigate alternative intracranial or ocular pathology"
        if dandy_criteria_met:
            if fulminant_iih:
                recommendation = f"CRITICAL FULMINANT IIH (LP Pressure {lp_opening_pressure_mm_h2o} mm H2O, Frisén Grade {frisen_papilledema_grade}): Threat of irreversible vision loss; urgent surgical intervention indicated ({recommended_treatment})"
            else:
                recommendation = f"Confirmed IIH (LP Pressure {lp_opening_pressure_mm_h2o} mm H2O, Frisén Grade {frisen_papilledema_grade}): Initiate Acetazolamide titration up to 4,000 mg/day + GLP-1 receptor agonist weight reduction protocol"

        return {
            "lp_opening_pressure_mm_h2o": lp_opening_pressure_mm_h2o,
            "frisen_papilledema_grade": frisen_papilledema_grade,
            "dandy_criteria_met": dandy_criteria_met,
            "fulminant_iih_vision_threat": fulminant_iih,
            "recommended_treatment": recommended_treatment,
            "clinical_recommendation": recommendation,
            "status": "EVALUATION_COMPLETE",
        }


# Singleton engine instance
iih_engine = IihDandyCriteriaEngine()
