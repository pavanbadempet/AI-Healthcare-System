"""
Transcatheter Edge-to-Edge Repair (TEER) Dual Mitral & Tricuspid Valve Combination Engine
==========================================================================================
Evaluates simultaneous vs staged dual-valve TEER (MitraClip/PASCAL Mitral + TriClip/PASCAL Tricuspid)
for patients with severe concomitant FMR and FTR with pulmonary hypertension assessment.
"""

from typing import Dict


class TeerMitralTricuspidCombinationEngine:
    """Evaluates dual mitral and tricuspid TEER strategy."""

    def evaluate_dual_teer_strategy(
        self,
        mitral_regurgitation_grade: int,  # 1 to 4 (3-4 = Severe)
        tricuspid_regurgitation_grade: int,  # 1 to 5 (3-5 = Severe/Torrential)
        systolic_pulmonary_artery_pressure_mmHg: float,  # sPAP > 50 mmHg = severe PHTN
        right_ventricular_function_tapse_mm: float,  # TAPSE < 17 mm = RV dysfunction
    ) -> Dict[str, any]:
        mitral_severe = mitral_regurgitation_grade >= 3
        tricuspid_severe = tricuspid_regurgitation_grade >= 3

        rv_dysfunction = right_ventricular_function_tapse_mm < 17.0
        severe_phtn = systolic_pulmonary_artery_pressure_mmHg > 50.0

        strategy = "SINGLE_VALVE_MITRAL_TEER"
        if mitral_severe and tricuspid_severe:
            if severe_phtn and rv_dysfunction:
                strategy = "STAGED_MITRAL_TEER_FIRST_THEN_REEVALUATE_TRICUSPID"
            else:
                strategy = "SIMULTANEOUS_DUAL_VALVE_MITRAL_AND_TRICUSPID_TEER"

        recommendation = "Single-valve TEER intervention indicated"
        if strategy == "SIMULTANEOUS_DUAL_VALVE_MITRAL_AND_TRICUSPID_TEER":
            recommendation = f"SIMULTANEOUS DUAL-VALVE TEER INDICATED (Severe MR Grade {mitral_regurgitation_grade} & Severe TR Grade {tricuspid_regurgitation_grade}): Perform MitraClip/PASCAL Mitral TEER followed immediately by TriClip/PASCAL Tricuspid TEER in same session"
        elif strategy == "STAGED_MITRAL_TEER_FIRST_THEN_REEVALUATE_TRICUSPID":
            recommendation = f"STAGED DUAL-VALVE STRATEGY RECOMMENDED (Severe PHTN {systolic_pulmonary_artery_pressure_mmHg} mmHg & RV TAPSE {right_ventricular_function_tapse_mm} mm): Perform Mitral TEER first to reduce left atrial pressure; recheck TR grade and RV remodeling at 3 months before Tricuspid TEER"

        return {
            "mitral_severe": mitral_severe,
            "tricuspid_severe": tricuspid_severe,
            "teer_strategy": strategy,
            "clinical_recommendation": recommendation,
            "status": "EVALUATION_COMPLETE",
        }


# Singleton engine instance
dual_teer_engine = TeerMitralTricuspidCombinationEngine()
