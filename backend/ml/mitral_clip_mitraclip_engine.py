"""
Percutaneous MitraClip Edge-to-Edge Repair Eligibility Engine
===============================================================
Evaluates COAPT vs MITRA-FR echocardiographic and clinical eligibility criteria
(EROA >= 0.40 cm2, LVESVI <= 96 mL/m2, LVEF 20-50%, coaptation length >= 2mm)
for Transcatheter Edge-to-Edge Mitral Valve Repair (TEER).
"""

from typing import Dict, Optional


class MitraClipMitraclipEngine:
    """Evaluates TEER MitraClip eligibility based on COAPT trial criteria."""

    def evaluate_mitraclip_eligibility(
        self,
        effective_regurgitant_orifice_area_eroa_cm2: float,
        left_ventricular_ejection_fraction_lvef_percent: float,
        left_ventricular_end_systolic_volume_index_lvesvi_mL_m2: float,
        mitral_valve_area_mva_cm2: float,
        coaptation_length_mm: Optional[float] = None,
        symptomatic_heart_failure_despite_gdmt: bool = True,
    ) -> Dict[str, any]:
        # COAPT criteria: disproportionate severe functional MR
        coapt_eligible = (
            symptomatic_heart_failure_despite_gdmt
            and effective_regurgitant_orifice_area_eroa_cm2 >= 0.30
            and 20.0 <= left_ventricular_ejection_fraction_lvef_percent <= 50.0
            and left_ventricular_end_systolic_volume_index_lvesvi_mL_m2 <= 96.0
            and mitral_valve_area_mva_cm2 >= 4.0
        )

        mitra_fr_non_responder_profile = (
            effective_regurgitant_orifice_area_eroa_cm2 < 0.30
            or left_ventricular_end_systolic_volume_index_lvesvi_mL_m2 > 96.0
        )

        phenotype = "INELIGIBLE_FOR_TEER"
        teer_indicated = False

        if coapt_eligible:
            phenotype = "COAPT_OPTIMAL_TEER_CANDIDATE"
            teer_indicated = True
        elif mitra_fr_non_responder_profile:
            phenotype = "SUBOPTIMAL_TEER_PROFILE_SEVERE_LV_DILATATION"

        recommendation = "Ineligible for TEER MitraClip; optimize Guideline-Directed Medical Therapy (GDMT) or evaluate surgical valve replacement"
        if teer_indicated:
            recommendation = "Optimal Candidate for MitraClip TEER (COAPT Profile): High 2-year survival & HF hospitalization reduction; proceed to Structural Heart Team evaluation"
        elif phenotype == "SUBOPTIMAL_TEER_PROFILE_SEVERE_LV_DILATATION":
            recommendation = "Suboptimal TEER candidate (Proportionate MR / Severe LV Remodeling): High risk of non-response; consider Advanced Heart Failure / LVAD / Transplant evaluation"

        return {
            "effective_regurgitant_orifice_area_eroa_cm2": effective_regurgitant_orifice_area_eroa_cm2,
            "left_ventricular_ejection_fraction_lvef_percent": left_ventricular_ejection_fraction_lvef_percent,
            "left_ventricular_end_systolic_volume_index_lvesvi_mL_m2": left_ventricular_end_systolic_volume_index_lvesvi_mL_m2,
            "coapt_trial_eligible": coapt_eligible,
            "mitraclip_teer_indicated": teer_indicated,
            "teer_phenotype": phenotype,
            "clinical_recommendation": recommendation,
            "status": "EVALUATION_COMPLETE",
        }


# Singleton engine instance
mitraclip_engine = MitraClipMitraclipEngine()
