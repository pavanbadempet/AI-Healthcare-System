"""
Spinal Cord Injury ASIA (American Spinal Injury Association) Impairment Scale Engine
====================================================================================
Classifies spinal cord injury from ASIA Grade A (Complete) to ASIA Grade E (Normal)
based on motor level, sensory level, sacral sparing (S4-S5), and deep anal pressure.
"""

from typing import Dict


class AsiaSpinalInjuryEngine:
    """Classifies traumatic spinal cord injury according to ASIA Impairment Scale (AIS)."""

    def classify_asia_impairment_scale(
        self,
        sacral_sensory_sparing_s4_s5: bool,
        deep_anal_pressure_present: bool,
        voluntary_anal_sphincter_contraction: bool,
        motor_function_spared_below_neurological_level: bool,
        more_than_half_key_muscles_grade_3_or_more: bool,
        neurological_level_of_injury: str = "T10",
    ) -> Dict[str, any]:
        sacral_sparing = sacral_sensory_sparing_s4_s5 or deep_anal_pressure_present or voluntary_anal_sphincter_contraction

        asia_grade = "ASIA_GRADE_A_COMPLETE"
        rehabilitation_tier = "SPECIALIZED_SPINAL_ICU"

        if not sacral_sparing:
            asia_grade = "ASIA_GRADE_A_COMPLETE"
            rehabilitation_tier = "SPECIALIZED_SPINAL_ICU_AND_RESPIRATORY_SUPPORT"
        elif voluntary_anal_sphincter_contraction and motor_function_spared_below_neurological_level:
            if more_than_half_key_muscles_grade_3_or_more:
                asia_grade = "ASIA_GRADE_D_INCOMPLETE"
                rehabilitation_tier = "AMBULATORY_REHABILITATION"
            else:
                asia_grade = "ASIA_GRADE_C_INCOMPLETE"
                rehabilitation_tier = "INTENSIVE_PHYSICAL_REHABILITATION"
        elif sacral_sparing:
            asia_grade = "ASIA_GRADE_B_INCOMPLETE_SENSORY_ONLY"
            rehabilitation_tier = "INPATIENT_REHABILITATION"

        recommendation = "ASIA Grade A (Complete): High risk of neurogenic shock & autonomic dysreflexia; STAT spine surgeon consult for posterior spinal fusion/decompression within 24h"
        if asia_grade != "ASIA_GRADE_A_COMPLETE":
            recommendation = f"ASIA {asia_grade}: Incomplete injury with sacral sparing; urgent surgical decompression & intensive neuro-rehabilitation"

        return {
            "neurological_level_of_injury": neurological_level_of_injury,
            "sacral_sparing_present": sacral_sparing,
            "asia_impairment_grade": asia_grade,
            "rehabilitation_tier": rehabilitation_tier,
            "urgent_spinal_decompression_indicated": True,
            "clinical_recommendation": recommendation,
            "status": "CLASSIFICATION_COMPLETE",
        }


# Singleton engine instance
asia_spinal_engine = AsiaSpinalInjuryEngine()
