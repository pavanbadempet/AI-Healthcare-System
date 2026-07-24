"""
Invasive Hemodynamic Cardiac Output & Fick Principle Engine
============================================================
Calculates Cardiac Output (CO) and Systemic Vascular Resistance (SVR)
from Swan-Ganz right heart catheterization data.
"""

from typing import Dict


class FickCardiacOutputEngine:
    """Calculates Cardiac Output (CO) and SVR via Fick Principle."""

    def calculate_fick_cardiac_output(
        self,
        oxygen_consumption_vo2_mL_min: float,
        hemoglobin_g_dL: float,
        arterial_sat_sao2_percent: float,
        mixed_venous_sat_svo2_percent: float,
        mean_arterial_pressure_mmHg: float,
        central_venous_pressure_mmHg: float,
    ) -> Dict[str, any]:
        # Cao2 = 1.34 * Hb * (SaO2 / 100)
        # Cvo2 = 1.34 * Hb * (SvO2 / 100)
        # CO (L/min) = (VO2 / 10) / (Cao2 - Cvo2)
        av_o2_diff = (1.34 * max(hemoglobin_g_dL, 0.1) * (arterial_sat_sao2_percent - mixed_venous_sat_svo2_percent)) / 100.0
        safe_av_o2_diff = max(av_o2_diff, 0.01)

        cardiac_output_L_min = round(oxygen_consumption_vo2_mL_min / (safe_av_o2_diff * 10.0), 2)

        # SVR (dynes*sec/cm5) = 80 * (MAP - CVP) / CO
        svr_dynes = round((80.0 * (mean_arterial_pressure_mmHg - central_venous_pressure_mmHg)) / max(cardiac_output_L_min, 0.1), 0)

        shock_state = "NORMAL_HEMODYNAMICS"
        if cardiac_output_L_min < 4.0 and svr_dynes > 1200:
            shock_state = "CARDIOGENIC_SHOCK"
        elif cardiac_output_L_min > 7.0 and svr_dynes < 800:
            shock_state = "DISTRIBUTIVE_SEPTIC_SHOCK"
        elif cardiac_output_L_min < 4.0 and svr_dynes < 800:
            shock_state = "MIXED_VASOPLEGIC_SHOCK"

        return {
            "cardiac_output_L_min": cardiac_output_L_min,
            "systemic_vascular_resistance_dynes": svr_dynes,
            "av_o2_difference_vol_pct": round(av_o2_diff, 2),
            "hemodynamic_shock_classification": shock_state,
            "status": "CALCULATION_COMPLETE",
        }


# Singleton engine instance
fick_engine = FickCardiacOutputEngine()
