"""
Invasive Tricuspid Valve TriClip / TEER Severity & Anatomical Selection Engine
================================================================================
Evaluates TriClip transcatheter tricuspid valve repair eligibility (TR grade Massive/Torrential,
coaptation gap <= 7mm, septal leaflet length >= 9mm, PASP <= 60 mmHg) for severe symptomatic TR.
"""

from typing import Dict, Optional


class TricuspidTriclipEngine:
    """Evaluates transcatheter tricuspid valve repair (TriClip TEER) eligibility."""

    def evaluate_triclip_eligibility(
        self,
        tricuspid_regurgitation_grade_1_to_5: int,  # 1:Mild, 2:Moderate, 3:Severe, 4:Massive, 5:Torrential
        coaptation_gap_mm: float,
        septal_leaflet_length_mm: float,
        pulmonary_artery_systolic_pressure_pasp_mmHg: float,
        right_ventricular_systolic_function_tapse_mm: Optional[float] = None,
        symptomatic_despite_diuretics: bool = True,
    ) -> Dict[str, any]:
        tr_severe_or_greater = tricuspid_regurgitation_grade_1_to_5 >= 3
        anatomically_favorable = (
            coaptation_gap_mm <= 7.0
            and septal_leaflet_length_mm >= 9.0
            and pulmonary_artery_systolic_pressure_pasp_mmHg <= 60.0
        )

        triclip_indicated = (
            symptomatic_despite_diuretics
            and tr_severe_or_greater
            and anatomically_favorable
        )

        phenotype = "INELIGIBLE_FOR_TRICLIP"
        if triclip_indicated:
            phenotype = "TRICLIP_TEER_OPTIMAL_CANDIDATE"
        elif tr_severe_or_greater and not anatomically_favorable:
            phenotype = "UNFAVORABLE_TRICUSPID_ANATOMY_SEVERE_PHTN_OR_GAP"

        recommendation = "Ineligible for TriClip TEER; optimize loop diuretic therapy & monitor right ventricular function"
        if triclip_indicated:
            recommendation = "Optimal Candidate for TriClip TEER: High likelihood of TR reduction to <= Moderate; refer for Structural Heart Team evaluation & TEE guidance"
        elif phenotype == "UNFAVORABLE_TRICUSPID_ANATOMY_SEVERE_PHTN_OR_GAP":
            recommendation = "Severe TR with Unfavorable TriClip Anatomy (Gap > 7mm or PASP > 60 mmHg): Evaluate for Transcatheter Tricuspid Valve Replacement (TTVR - Evoque) or Surgical Repair"

        return {
            "tr_severity_grade": tricuspid_regurgitation_grade_1_to_5,
            "coaptation_gap_mm": coaptation_gap_mm,
            "septal_leaflet_length_mm": septal_leaflet_length_mm,
            "pasp_mmHg": pulmonary_artery_systolic_pressure_pasp_mmHg,
            "triclip_teer_indicated": triclip_indicated,
            "anatomically_favorable": anatomically_favorable,
            "tricuspid_repair_phenotype": phenotype,
            "clinical_recommendation": recommendation,
            "status": "EVALUATION_COMPLETE",
        }


# Singleton engine instance
triclip_engine = TricuspidTriclipEngine()
