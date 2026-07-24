"""
TPVR Alterra Adaptive Prestent Sizing Engine for Large RVOT
===========================================================
Evaluates dilated native RVOT (27-38 mm diameter) in Tetralogy of Fallot post-transannular patch repair
for Alterra Adaptive Prestent deployment to reduce landing zone diameter to 27 mm for SAPIEN 3 valve insertion.
"""

from typing import Dict


class TpvrAlterraAdaptivePrestentEngine:
    """Evaluates Alterra Adaptive Prestent for large RVOT in TPVR candidacy."""

    def evaluate_alterra_candidacy(
        self,
        native_rvot_diameter_mm: float,  # 27.0 to 38.0 mm
        severe_pulmonary_regurgitation: bool = True,
        post_tetralogy_of_fallot_repair: bool = True,
        coronary_compression_risk: bool = False,
    ) -> Dict[str, any]:
        if coronary_compression_risk:
            return {
                "alterra_eligible": False,
                "reason": "CORONARY_COMPRESSION_RISK",
                "clinical_recommendation": "ALTERRA PRESTENT CONTRAINDICATED! Coronary artery compression risk identified on balloon interrogation; refer for open surgical RVOT reconstruction",
                "status": "EVALUATION_COMPLETE",
            }

        eligible = (
            severe_pulmonary_regurgitation
            and 27.0 <= native_rvot_diameter_mm <= 38.0
            and not coronary_compression_risk
        )

        recommendation = "Alterra Adaptive Prestent NOT indicated (RVOT diameter outside 27-38 mm range); evaluate standard SAPIEN 3 / Melody or surgical RVOT repair"
        if eligible:
            recommendation = f"ELIGIBLE FOR ALTERRA ADAPTIVE PRESTENT (RVOT {native_rvot_diameter_mm} mm): Deploy self-expanding Nitinol Alterra Adaptive Prestent in dilated RVOT to create a uniform 27 mm landing zone, followed immediately by 29 mm Edwards SAPIEN 3 valve deployment"

        return {
            "alterra_eligible": eligible,
            "native_rvot_diameter_mm": native_rvot_diameter_mm,
            "recommended_prestent": "ALTERRA_ADAPTIVE_PRESTENT_PLUS_SAPIEN_3_29MM" if eligible else "NONE",
            "clinical_recommendation": recommendation,
            "status": "EVALUATION_COMPLETE",
        }


# Singleton engine instance
alterra_engine = TpvrAlterraAdaptivePrestentEngine()
