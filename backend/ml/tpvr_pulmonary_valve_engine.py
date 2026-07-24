"""
Transcatheter Pulmonary Valve Replacement (TPVR) Melody vs SAPIEN 3 Sizing Engine
===================================================================================
Evaluates RVOT dysfunction (severe PR > 35%, RVEDVI > 150 mL/m2, RVOT gradient > 35 mmHg)
and RVOT landing zone diameter to select Melody valve (16-22 mm) vs SAPIEN 3 (20-29 mm) vs Alterra / VenusP-Valve.
"""

from typing import Dict


class TpvrPulmonaryValveEngine:
    """Evaluates TPVR candidacy and device selection for RVOT dysfunction."""

    def evaluate_tpvr_suitability(
        self,
        rvot_landing_zone_diameter_mm: float,  # 16-22 mm (Melody), 20-29 mm (SAPIEN 3), > 29 mm (Alterra/VenusP)
        severe_pulmonary_regurgitation_percent: float = 40.0,  # > 35%
        rv_end_diastolic_volume_index_mL_m2: float = 160.0,  # > 150 mL/m2
        coronary_compression_risk_on_balloon_sizing: bool = False,
    ) -> Dict[str, any]:
        rvot_dysfunction_present = (
            severe_pulmonary_regurgitation_percent >= 35.0 or rv_end_diastolic_volume_index_mL_m2 >= 150.0
        )

        tpvr_eligible = rvot_dysfunction_present and not coronary_compression_risk_on_balloon_sizing

        device = "NONE"
        if tpvr_eligible:
            if 16.0 <= rvot_landing_zone_diameter_mm <= 22.0:
                device = "MELODY_VALVE_16_TO_22MM"
            elif 20.0 <= rvot_landing_zone_diameter_mm <= 29.0:
                device = "EDWARDS_SAPIEN_3_VALVE_20_TO_29MM"
            elif rvot_landing_zone_diameter_mm > 29.0:
                device = "ALTERRA_ADAPTIVE_PRESTENT_OR_VENUSP_VALVE"

        recommendation = "TPVR NOT indicated or CONTRAINDICATED due to high coronary artery compression risk during balloon interrogation; surgical RVOT reconstruction required"
        if tpvr_eligible:
            recommendation = f"ELIGIBLE FOR TPVR (RVOT diameter {rvot_landing_zone_diameter_mm} mm, PR {severe_pulmonary_regurgitation_percent}%): Deploy {device} under fluoroscopic and angiographic guidance to restore pulmonary valve competence and promote RV reverse remodeling"

        return {
            "rvot_dysfunction_present": rvot_dysfunction_present,
            "coronary_compression_risk": coronary_compression_risk_on_balloon_sizing,
            "tpvr_eligible": tpvr_eligible,
            "recommended_device": device,
            "clinical_recommendation": recommendation,
            "status": "EVALUATION_COMPLETE",
        }


# Singleton engine instance
tpvr_engine = TpvrPulmonaryValveEngine()
