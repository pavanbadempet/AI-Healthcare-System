"""
Transcatheter Pulmonary Valve Replacement (TPVR) RVOT Anatomy & System Sizing Engine
======================================================================================
Evaluates RVOT anatomy (patched vs conduit), RVEDVI, pulmonary regurgitation fraction,
and RVOT diameter to select Melody TPV vs SAPIEN 3 vs Harmony TPVR valve.
"""

from typing import Dict


class TpvrRvotAnatomyEngine:
    """Evaluates RVOT anatomical suitability and valve selection for TPVR."""

    def evaluate_tpvr_suitability(
        self,
        rvot_anatomy_type: str,  # NATIVE_PATCHED_RVOT, CONDUIT, FAILED_BIOPROSTHETIC_VALVE
        rvot_waist_diameter_mm: float,
        pulmonary_regurgitation_fraction_percent: float = 40.0,
        rvedvi_mL_m2: float = 160.0,  # > 150 mL/m2 = indication for intervention
    ) -> Dict[str, any]:
        tpvr_indicated = (pulmonary_regurgitation_fraction_percent >= 35.0 and rvedvi_mL_m2 >= 150.0) or (rvot_anatomy_type == "FAILED_BIOPROSTHETIC_VALVE")

        recommended_valve_system = "MEDTRONIC_HARMONY_TPVR_22MM_OR_25MM"
        if rvot_anatomy_type == "CONDUIT":
            if rvot_waist_diameter_mm <= 22.0:
                recommended_valve_system = "MELODY_TPV_SYSTEM"
            else:
                recommended_valve_system = "EDWARDS_SAPIEN_3_26MM_OR_29MM"
        elif rvot_anatomy_type == "FAILED_BIOPROSTHETIC_VALVE":
            recommended_valve_system = "EDWARDS_SAPIEN_3_VALVE_IN_VALVE"

        recommendation = "TPVR not indicated (Pulmonary regurgitation fraction < 35% and RVEDVI < 150 mL/m2); continue annual MRI surveillance"
        if tpvr_indicated:
            recommendation = f"TPVR INDICATED ({rvot_anatomy_type}, RVEDVI {rvedvi_mL_m2} mL/m2): Recommend {recommended_valve_system}. Perform pre-procedural coronary compression testing with high-pressure balloon inflation in RVOT"

        return {
            "tpvr_indicated": tpvr_indicated,
            "rvot_anatomy_type": rvot_anatomy_type,
            "recommended_valve_system": recommended_valve_system if tpvr_indicated else "NONE",
            "clinical_recommendation": recommendation,
            "status": "EVALUATION_COMPLETE",
        }


# Singleton engine instance
tpvr_anatomy_engine = TpvrRvotAnatomyEngine()
