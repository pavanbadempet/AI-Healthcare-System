"""
Infective Endocarditis Embolic Risk (EORIST) & Surgical Timing Engine
======================================================================
Evaluates vegetation length (>= 10 mm high risk, >= 15 mm critical risk), mobility,
Staphylococcus aureus / fungal microbiology, and valvular destruction on TEE to guide
urgent early surgery vs 6-week parenteral antimicrobial therapy.
"""

from typing import Dict


class EndocarditisEmbolicRiskEngine:
    """Evaluates embolic risk and early surgical intervention criteria in infective endocarditis."""

    def evaluate_embolic_risk_and_surgery(
        self,
        vegetation_max_length_mm: float,
        mobile_vegetation: bool,
        staph_aureus_or_fungal_microbiology: bool,
        prior_embolic_event: bool = False,
        severe_valvular_regurgitation_heart_failure: bool = False,
        paravalvular_abscess_or_fistula: bool = False,
    ) -> Dict[str, any]:
        embolic_risk_score = 0

        if vegetation_max_length_mm >= 15.0:
            embolic_risk_score += 4
        elif vegetation_max_length_mm >= 10.0:
            embolic_risk_score += 2

        if mobile_vegetation:
            embolic_risk_score += 2
        if staph_aureus_or_fungal_microbiology:
            embolic_risk_score += 2
        if prior_embolic_event:
            embolic_risk_score += 3

        urgent_surgery_indicated = (
            severe_valvular_regurgitation_heart_failure
            or paravalvular_abscess_or_fistula
            or (vegetation_max_length_mm >= 15.0 and mobile_vegetation)
            or (vegetation_max_length_mm >= 10.0 and prior_embolic_event)
        )

        surgical_timing = "CONSERVATIVE_MEDICAL_ANTIMICROBIAL_MANAGEMENT"
        if urgent_surgery_indicated:
            if severe_valvular_regurgitation_heart_failure or paravalvular_abscess_or_fistula:
                surgical_timing = "EMERGENT_VALVE_SURGERY_WITHIN_24_HOURS"
            else:
                surgical_timing = "URGENT_VALVE_SURGERY_DURING_INDEX_HOSPITALIZATION"

        recommendation = "Low embolic risk: Continue 4-6 weeks target parenteral antimicrobial therapy (e.g. Vancomycin + Cefepime); repeat TEE in 7 days"
        if urgent_surgery_indicated:
            if surgical_timing == "EMERGENT_VALVE_SURGERY_WITHIN_24_HOURS":
                recommendation = f"EMERGENT SURGICAL INDICATION (Heart Failure / Abscess): Perform valve repair/replacement within 24 hours to prevent refractory shock (Embolic Risk Score {embolic_risk_score})"
            else:
                recommendation = f"URGENT SURGICAL INDICATION (Vegetation {vegetation_max_length_mm} mm + High Embolic Risk Score {embolic_risk_score}): Perform early valve surgery during index admission to prevent recurrent embolic stroke"

        return {
            "vegetation_length_mm": vegetation_max_length_mm,
            "embolic_risk_score": embolic_risk_score,
            "urgent_surgery_indicated": urgent_surgery_indicated,
            "recommended_surgical_timing": surgical_timing,
            "clinical_recommendation": recommendation,
            "status": "EVALUATION_COMPLETE",
        }


# Singleton engine instance
endocarditis_engine = EndocarditisEmbolicRiskEngine()
