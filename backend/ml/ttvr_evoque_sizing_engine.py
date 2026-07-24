"""
Percutaneous Tricuspid Valve Replacement (TTVR) EVOQUE Sizing Engine
====================================================================
Evaluates 4D Cardiac CT / 3D TEE tricuspid annulus perimeter (100-145 mm), area,
and IVC/hepatic vein reflux to size EVOQUE TTVR valve prostheses (44mm, 48mm, 52mm)
for severe tricuspid regurgitation in non-TEER candidates.
"""

from typing import Dict, Optional


class TtvrEvoqueSizingEngine:
    """Evaluates anatomical and hemodynamic parameters for TTVR EVOQUE valve sizing."""

    def evaluate_ttvr_evoque_eligibility(
        self,
        tricuspid_annulus_perimeter_mm: float,
        tricuspid_annulus_area_cm2: float,
        ivc_diameter_mm: float,
        severe_tricuspid_regurgitation: bool = True,
        anatomically_suitable_for_triclip: bool = False,
    ) -> Dict[str, any]:
        eligible = (
            severe_tricuspid_regurgitation
            and not anatomically_suitable_for_triclip
            and (100.0 <= tricuspid_annulus_perimeter_mm <= 145.0)
            and (ivc_diameter_mm <= 34.0)
        )

        recommended_evoque_size_mm: Optional[int] = None
        if eligible:
            if tricuspid_annulus_perimeter_mm <= 115.0:
                recommended_evoque_size_mm = 44
            elif tricuspid_annulus_perimeter_mm <= 130.0:
                recommended_evoque_size_mm = 48
            else:
                recommended_evoque_size_mm = 52

        phenotype = "INELIGIBLE_FOR_TTVR"
        if eligible:
            phenotype = "EVOQUE_TTVR_CANDIDATE"
        elif anatomically_suitable_for_triclip:
            phenotype = "PREFER_TRICLIP_TEER"
        elif tricuspid_annulus_perimeter_mm > 145.0:
            phenotype = "ANATOMICAL_ANNULAR_OVERSIZING"

        recommendation = "Ineligible for TTVR EVOQUE valve replacement"
        if phenotype == "EVOQUE_TTVR_CANDIDATE":
            recommendation = f"Candidate for TTVR EVOQUE ({recommended_evoque_size_mm} mm prosthesis): Transfemoral delivery indicated; evaluate right ventricular systolic function (TAPSE >= 14 mm) prior to deployment"
        elif phenotype == "PREFER_TRICLIP_TEER":
            recommendation = "Anatomy favorable for TriClip TEER repair; reserve TTVR for secondary option"

        return {
            "annulus_perimeter_mm": tricuspid_annulus_perimeter_mm,
            "annulus_area_cm2": tricuspid_annulus_area_cm2,
            "ttvr_eligible": eligible,
            "recommended_evoque_size_mm": recommended_evoque_size_mm,
            "ttvr_phenotype": phenotype,
            "clinical_recommendation": recommendation,
            "status": "EVALUATION_COMPLETE",
        }


# Singleton engine instance
ttvr_engine = TtvrEvoqueSizingEngine()
