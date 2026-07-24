"""
Chronic Hepatitis B Tenofovir Alafenamide (TAF) Renal & Bone Safety Engine
============================================================================
Evaluates eGFR (< 60 mL/min), osteopenia/osteoporosis, age > 60, and prior TDF exposure
to guide switching from TDF to TAF (25 mg daily) or Entecavir (0.5 mg daily).
"""

from typing import Dict


class HepatitisBTafRenalBoneSafetyEngine:
    """Evaluates TDF to TAF or Entecavir switch indications for Chronic HBV."""

    def evaluate_taf_switch_indication(
        self,
        current_antiviral: str,  # TDF, TAF, ENTECAVIR, NONE
        egfr_mL_min_1_73m2: float,
        bone_mineral_density_t_score: float = 0.0,  # <= -2.5 = osteoporosis
        age_years: int = 45,
        history_of_fragility_fracture: bool = False,
        proteinuria_present: bool = False,
    ) -> Dict[str, any]:
        renal_impairment = egfr_mL_min_1_73m2 < 60.0 or proteinuria_present
        bone_disease = bone_mineral_density_t_score <= -2.0 or history_of_fragility_fracture
        elderly_age = age_years >= 60

        switch_indicated = (current_antiviral == "TDF") and (renal_impairment or bone_disease or elderly_age)

        recommended_alternative = "TAF_25MG_DAILY"
        if egfr_mL_min_1_73m2 < 15.0:  # End-stage renal disease without hemodialysis
            recommended_alternative = "ENTECAVIR_DOSE_ADJUSTED"

        recommendation = f"Continue current antiviral ({current_antiviral}): Renal function (eGFR {egfr_mL_min_1_73m2} mL/min) and Bone density (T-score {bone_mineral_density_t_score}) stable"
        if switch_indicated:
            recommendation = f"SWITCH FROM TDF INDICATED ({'Renal impairment' if renal_impairment else 'Bone disease / Age >= 60'}): Switch from TDF to {recommended_alternative} to reduce nephrotoxicity and bone mineral density loss"

        return {
            "current_antiviral": current_antiviral,
            "renal_impairment_present": renal_impairment,
            "bone_disease_present": bone_disease,
            "switch_from_tdf_indicated": switch_indicated,
            "recommended_alternative_antiviral": recommended_alternative if switch_indicated else "NONE",
            "clinical_recommendation": recommendation,
            "status": "EVALUATION_COMPLETE",
        }


# Singleton engine instance
hbv_taf_engine = HepatitisBTafRenalBoneSafetyEngine()
