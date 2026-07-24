"""
Invasive Coronary Microvascular Dysfunction (CMD) Index of Microvascular Resistance (IMR) Engine
================================================================================================
Calculates IMR (Pd * Tmn at maximal hyperemia) and Coronary Flow Reserve (CFR)
to diagnose Coronary Microvascular Dysfunction in ANOCA/INOCA patients.
"""

from typing import Dict, Optional


class ImrCoronaryMicrovascularEngine:
    """Evaluates invasive IMR and CFR measurements for microvascular angina."""

    def evaluate_microvascular_function(
        self,
        distal_pressure_hyperemia_pd_mmHg: float,
        mean_transit_time_hyperemia_sec: float,
        coronary_flow_reserve_cfr: Optional[float] = None,
    ) -> Dict[str, any]:
        # IMR = Pd_hyperemia * Tmn_hyperemia
        imr_value = round(distal_pressure_hyperemia_pd_mmHg * mean_transit_time_hyperemia_sec, 1)

        cmd_present = imr_value > 25.0
        abnormal_cfr = coronary_flow_reserve_cfr is not None and coronary_flow_reserve_cfr <= 2.0

        phenotype = "NORMAL_MICROVASCULAR_FUNCTION"
        if cmd_present and abnormal_cfr:
            phenotype = "STRUCTURAL_AND_FUNCTIONAL_CMD"
        elif cmd_present:
            phenotype = "STRUCTURAL_CORONARY_MICROVASCULAR_DYSFUNCTION"
        elif abnormal_cfr:
            phenotype = "FUNCTIONAL_VASOSPASTIC_OR_ENDOTHELIAL_CMD"

        recommendation = "Normal IMR/CFR: Reassure patient & screen for non-cardiac chest pain"
        if cmd_present or abnormal_cfr:
            recommendation = "ANOCA/INOCA Confirmed: Initiate Microvascular Angina therapy (Beta-Blockers / Diltiazem + ACEi/ARB + High-Intensity Statin + Lifestyle)"

        return {
            "index_of_microvascular_resistance_imr": imr_value,
            "coronary_flow_reserve_cfr": coronary_flow_reserve_cfr,
            "coronary_microvascular_dysfunction_cmd": cmd_present or abnormal_cfr,
            "anoca_inoca_phenotype": phenotype,
            "medical_therapy_indicated": cmd_present or abnormal_cfr,
            "clinical_recommendation": recommendation,
            "status": "EVALUATION_COMPLETE",
        }


# Singleton engine instance
imr_coronary_engine = ImrCoronaryMicrovascularEngine()
