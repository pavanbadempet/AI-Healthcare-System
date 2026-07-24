"""
Cardiogenic Shock SCAI Staging Engine
=====================================
Stages cardiogenic shock from Stage A (At Risk) to Stage E (Extremis) based on lactate,
cardiac index, and mechanical circulatory support requirement.
"""

from typing import Dict


class ScaiCardiogenicShockEngine:
    """Stages cardiogenic shock according to SCAI clinical criteria."""

    def stage_cardiogenic_shock(
        self,
        systolic_bp_mmHg: int,
        lactate_mmol_L: float,
        cardiac_index_L_min_m2: float,
        on_inotropes_or_vasopressors: bool = False,
        on_mechanical_circulatory_support: bool = False,  # Impella / IABP / VA-ECMO
        cardiac_arrest_refractory: bool = False,
    ) -> Dict[str, any]:
        stage = "STAGE_A_AT_RISK"

        if cardiac_arrest_refractory:
            stage = "STAGE_E_EXTREMIS"
        elif on_mechanical_circulatory_support or (on_inotropes_or_vasopressors and lactate_mmol_L > 4.0):
            stage = "STAGE_D_DETERIORATING"
        elif on_inotropes_or_vasopressors or lactate_mmol_L > 2.0 or cardiac_index_L_min_m2 < 2.2:
            stage = "STAGE_C_CLASSIC"
        elif systolic_bp_mmHg < 90 or lactate_mmol_L > 1.5:
            stage = "STAGE_B_BEGINNING"

        recommendation = "Standard hemodynamic surveillance"
        if stage in ["STAGE_D_DETERIORATING", "STAGE_E_EXTREMIS"]:
            recommendation = "Stat Shock Team Activation & consider Impella CP / VA-ECMO mechanical circulatory support"
        elif stage == "STAGE_C_CLASSIC":
            recommendation = "Initiate IV Inotropes (Dobutamine/Milrinone) & invasive PAC (Pulmonary Artery Catheter) monitoring"

        return {
            "scai_shock_stage": stage,
            "lactate_mmol_L": lactate_mmol_L,
            "shock_team_activation_indicated": stage in ["STAGE_C_CLASSIC", "STAGE_D_DETERIORATING", "STAGE_E_EXTREMIS"],
            "clinical_recommendation": recommendation,
            "status": "STAGING_COMPLETE",
        }


# Singleton engine instance
scai_shock_engine = ScaiCardiogenicShockEngine()
