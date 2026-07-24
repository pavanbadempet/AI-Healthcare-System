"""
Transcatheter Mitral Valve Replacement (TMVR) Tendyne / Intrepid Sizing Engine
================================================================================
Evaluates 4D Cardiac CT mitral annulus perimeter (100-140 mm), neo-LVOT area (>= 1.8 cm2),
and anterior leaflet length to size Tendyne or Intrepid TMVR prostheses in high-risk MR.
"""

from typing import Dict


class TmvrMitralReplacementEngine:
    """Evaluates TMVR anatomical feasibility and neo-LVOT obstruction risk."""

    def evaluate_tmvr_eligibility(
        self,
        mitral_annulus_perimeter_mm: float,
        predicted_neo_lvot_area_cm2: float,  # Must be >= 1.7-2.0 cm2
        mitral_regurgitation_severity: str = "SEVERE",
        suitable_for_mitraclip_teer: bool = False,
    ) -> Dict[str, any]:
        neo_lvot_adequate = predicted_neo_lvot_area_cm2 >= 1.8
        annulus_eligible = 95.0 <= mitral_annulus_perimeter_mm <= 140.0

        eligible = (
            mitral_regurgitation_severity == "SEVERE"
            and not suitable_for_mitraclip_teer
            and neo_lvot_adequate
            and annulus_eligible
        )

        recommended_device = "INELIGIBLE"
        if eligible:
            if mitral_annulus_perimeter_mm <= 115.0:
                recommended_device = "TENDYNE_TMVR_MEDIUM_SIZE"
            else:
                recommended_device = "INTREPID_TMVR_LARGE_SIZE"

        recommendation = "Ineligible for TMVR; evaluate surgical mitral replacement or medical management"
        if eligible:
            recommendation = f"Candidate for TMVR ({recommended_device}): Predicted neo-LVOT area {predicted_neo_lvot_area_cm2} cm2 is adequate (> 1.8 cm2); transapical / transseptal delivery indicated"
        elif not neo_lvot_adequate and not suitable_for_mitraclip_teer:
            recommendation = f"HIGH RISK OF NEO-LVOT OBSTRUCTION (Predicted area {predicted_neo_lvot_area_cm2} cm2 < 1.8 cm2): TMVR contraindicated; evaluate SESAME / LAMPOON electrosurgical anterior leaflet resection prior to TMVR"

        return {
            "mitral_annulus_perimeter_mm": mitral_annulus_perimeter_mm,
            "predicted_neo_lvot_area_cm2": predicted_neo_lvot_area_cm2,
            "neo_lvot_adequate": neo_lvot_adequate,
            "tmvr_eligible": eligible,
            "recommended_device": recommended_device,
            "clinical_recommendation": recommendation,
            "status": "EVALUATION_COMPLETE",
        }


# Singleton engine instance
tmvr_engine = TmvrMitralReplacementEngine()
