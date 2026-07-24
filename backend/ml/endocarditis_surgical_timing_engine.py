"""
Infective Endocarditis Surgical Timing & Urgent Indication Engine
=================================================================
Evaluates indications for emergency (< 24h) vs urgent (< 7d) cardiac surgery in acute infective endocarditis:
refractory heart failure / acute aortic valve destruction, perivalvular abscess/fistula, persistent vegetation > 10 mm
with embolic events despite antimicrobial therapy, and fungal endocarditis (Candida, Aspergillus).
"""

from typing import Dict


class EndocarditisSurgicalTimingEngine:
    """Evaluates surgical timing and emergency vs urgent operative indications in infective endocarditis."""

    def evaluate_surgical_timing(
        self,
        acute_heart_failure_or_cardiogenic_shock: bool,  # Refractory HF from severe AR/MR
        perivalvular_abscess_or_fistula: bool,  # Uncontrolled local infection
        fungal_endocarditis: bool,  # Candida / Aspergillus
        vegetation_size_mm: float,  # > 10 mm high risk for embolic stroke
        recurrent_embolic_events: bool,  # Embolic stroke, splenic infarction, septic pulmonary emboli
        days_on_adequate_antibiotics: int,
    ) -> Dict[str, any]:
        is_emergency = acute_heart_failure_or_cardiogenic_shock or perivalvular_abscess_or_fistula
        is_urgent = (
            fungal_endocarditis
            or (vegetation_size_mm > 10.0 and recurrent_embolic_events)
            or (vegetation_size_mm > 15.0 and days_on_adequate_antibiotics >= 3)
        )

        timing_category = "ELECTIVE_OR_MEDICAL_ONLY"
        recommendation = "CONTINUE MEDICAL ANTIMICROBIAL THERAPY: Patient does not currently meet emergency or urgent surgical criteria. Repeat TEE in 7-10 days."

        if is_emergency:
            timing_category = "EMERGENCY_SURGERY_WITHIN_24H"
            recommendation = "EMERGENCY SURGERY MANDATED (< 24 HOURS): Immediate cardiac surgery consultation for valve replacement / annular debridement due to refractory heart failure or perivalvular abscess / fistula."
        elif is_urgent:
            timing_category = "URGENT_SURGERY_WITHIN_7_DAYS"
            recommendation = "URGENT SURGERY MANDATED (< 7 DAYS): Schedule operative intervention during current hospital admission due to fungal endocarditis or large vegetation (> 10 mm) with embolic complications."

        return {
            "is_emergency_indicated": is_emergency,
            "is_urgent_indicated": is_urgent,
            "timing_category": timing_category,
            "vegetation_size_mm": vegetation_size_mm,
            "clinical_recommendation": recommendation,
            "status": "EVALUATION_COMPLETE",
        }


# Singleton engine instance
endocarditis_surgical_engine = EndocarditisSurgicalTimingEngine()
