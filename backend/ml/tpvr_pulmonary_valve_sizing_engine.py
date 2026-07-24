"""
Transcatheter Pulmonary Valve Replacement (TPVR) Harmony / Melody Engine
========================================================================
Evaluates 4D Cardiac CT / MRI RVOT diameter (16-32 mm), pulmonary regurgitation fraction (>= 35%),
and RVEDVI (>= 150 mL/m2) to size Harmony TPV or Melody TPV in repaired Tetralogy of Fallot (ToF).
"""

from typing import Dict, Optional


class TpvrPulmonaryValveSizingEngine:
    """Evaluates RVOT anatomy and hemodynamics for TPVR valve selection."""

    def evaluate_tpvr_eligibility(
        self,
        rvot_max_diameter_mm: float,
        pulmonary_regurgitation_fraction_pct: float,
        rvedvi_mL_m2: float,
        conduit_type: str = "NATIVE_RVOT",  # NATIVE_RVOT, HOMOGRAFT, BIOPROSTHETIC_VALVE
        coronary_compression_risk: bool = False,
    ) -> Dict[str, any]:
        eligible = (
            not coronary_compression_risk
            and (pulmonary_regurgitation_fraction_pct >= 35.0 or rvedvi_mL_m2 >= 150.0)
            and (16.0 <= rvot_max_diameter_mm <= 32.0)
        )

        recommended_valve = "INELIGIBLE"
        recommended_size_mm: Optional[int] = None

        if eligible:
            if conduit_type in ["HOMOGRAFT", "BIOPROSTHETIC_VALVE"] and rvot_max_diameter_mm <= 22.0:
                recommended_valve = "MELODY_TPV"
                recommended_size_mm = 18 if rvot_max_diameter_mm <= 18.0 else 22
            elif rvot_max_diameter_mm <= 26.0:
                recommended_valve = "HARMONY_TPV_22MM"
                recommended_size_mm = 22
            else:
                recommended_valve = "HARMONY_TPV_25MM"
                recommended_size_mm = 25

        recommendation = "Ineligible for TPVR; evaluate surgical RVOT reconstruction or medical management"
        if eligible:
            if coronary_compression_risk:
                recommendation = "CRITICAL CONTRAINDICATION: High risk of coronary artery compression during balloon inflation; TPVR contraindicated"
            else:
                recommendation = f"Candidate for TPVR ({recommended_valve}): Transfemoral / Transjugular access indicated; perform pre-stenting balloon occlusion test to confirm coronary clearance"

        return {
            "rvot_max_diameter_mm": rvot_max_diameter_mm,
            "pulmonary_regurgitation_fraction_pct": pulmonary_regurgitation_fraction_pct,
            "rvedvi_mL_m2": rvedvi_mL_m2,
            "tpvr_eligible": eligible,
            "recommended_valve": recommended_valve,
            "recommended_size_mm": recommended_size_mm,
            "clinical_recommendation": recommendation,
            "status": "EVALUATION_COMPLETE",
        }


# Singleton engine instance
tpvr_engine = TpvrPulmonaryValveSizingEngine()
