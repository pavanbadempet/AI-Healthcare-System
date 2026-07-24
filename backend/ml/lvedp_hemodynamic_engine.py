"""
Invasive Left Ventricular End-Diastolic Pressure (LVEDP) Engine
================================================================
Calculates LVEDP and pulmonary capillary wedge pressure (PCWP)
to differentiate HFpEF from precapillary Pulmonary Arterial Hypertension (PAH).
"""

from typing import Dict


class LvedpHemodynamicEngine:
    """Evaluates invasive catheterization LVEDP and PCWP measurements."""

    def evaluate_lvedp_hemodynamics(
        self,
        lvedp_mmHg: float,
        pcwp_mmHg: float,
        mean_pap_mmHg: float,
        pulmonary_vascular_resistance_wood_units: float = 2.0,
    ) -> Dict[str, any]:
        elevated_filling_pressure = lvedp_mmHg > 16.0 or pcwp_mmHg > 15.0
        precapillary_pah = mean_pap_mmHg > 20.0 and pcwp_mmHg <= 15.0 and pulmonary_vascular_resistance_wood_units > 2.0

        classification = "NORMAL_LEFT_HEART_FILLING_PRESSURES"
        if precapillary_pah:
            classification = "PRECAPILLARY_PULMONARY_ARTERIAL_HYPERTENSION"
        elif elevated_filling_pressure:
            classification = "POSTCAPILLARY_HFPEF_LEFT_HEART_DISEASE"

        recommendation = "Standard hemodynamic surveillance"
        if classification == "POSTCAPILLARY_HFPEF_LEFT_HEART_DISEASE":
            recommendation = "Elevated LVEDP/PCWP: Initiate SGLT2 inhibitor (Empagliflozin/Dapagliflozin) & Loop Diuretics for HFpEF decongestion"
        elif classification == "PRECAPILLARY_PULMONARY_ARTERIAL_HYPERTENSION":
            recommendation = "Precapillary PAH confirmed: Refer to Pulmonary Hypertension Center for ERA + PDE5i vasodilator therapy"

        return {
            "lvedp_mmHg": lvedp_mmHg,
            "pcwp_mmHg": pcwp_mmHg,
            "elevated_filling_pressures": elevated_filling_pressure,
            "hemodynamic_classification": classification,
            "sglt2i_and_diuretics_indicated": classification == "POSTCAPILLARY_HFPEF_LEFT_HEART_DISEASE",
            "clinical_recommendation": recommendation,
            "status": "EVALUATION_COMPLETE",
        }


# Singleton engine instance
lvedp_engine = LvedpHemodynamicEngine()
