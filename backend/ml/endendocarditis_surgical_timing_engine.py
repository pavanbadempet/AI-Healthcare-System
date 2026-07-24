"""
Infective Endocarditis Surgical Timing & Indications Engine
============================================================
Evaluates 2023 ESC / ACC/AHA Endocarditis Guidelines for Emergency (< 24h), Urgent (< 7 days),
or Elective valve surgery based on heart failure, persistent infection, and embolic risk.
"""

from typing import Dict


class EndocarditisSurgicalTimingEngine:
    """Evaluates surgical indication and timing for Infective Endocarditis."""

    def evaluate_surgical_timing(
        self,
        refractory_heart_failure_shock: bool = False,
        sinus_of_valsalva_annular_abscess_rupture: bool = False,
        fungal_or_multi_drug_resistant_organism: bool = False,
        persistent_bacteremia_beyond_7_days: bool = False,
        vegetation_length_mm: float = 8.0,
        recurrent_embolic_events_on_antibiotics: bool = False,
    ) -> Dict[str, any]:
        emergency_indication = refractory_heart_failure_shock or sinus_of_valsalva_annular_abscess_rupture
        urgent_indication = (
            fungal_or_multi_drug_resistant_organism
            or persistent_bacteremia_beyond_7_days
            or (vegetation_length_mm >= 10.0 and recurrent_embolic_events_on_antibiotics)
            or vegetation_length_mm >= 15.0
        )

        timing = "ELECTIVE_OR_MEDICAL_THERAPY"
        surgery_indicated = False

        if emergency_indication:
            timing = "EMERGENCY_SURGERY_WITHIN_24_HOURS"
            surgery_indicated = True
        elif urgent_indication:
            timing = "URGENT_SURGERY_WITHIN_7_DAYS"
            surgery_indicated = True

        recommendation = "Continue targeted IV antimicrobial therapy; reassess daily for heart failure or embolic complications"
        if surgery_indicated:
            recommendation = f"SURGERY INDICATED ({timing}): Multidisciplinary Endocarditis Team evaluation for operative valve debridement and reconstruction"

        return {
            "surgery_indicated": surgery_indicated,
            "surgical_timing": timing,
            "vegetation_length_mm": vegetation_length_mm,
            "clinical_recommendation": recommendation,
            "status": "EVALUATION_COMPLETE",
        }


# Singleton engine instance
endocarditis_timing_engine = EndocarditisSurgicalTimingEngine()
