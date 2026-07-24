"""
Myasthenic Crisis Extubation Readiness & Respiratory Parameters Engine
========================================================================
Evaluates Negative Inspiratory Force (NIF <= -30 cmH2O), Vital Capacity (FVC >= 15-20 mL/kg),
Maximum Expiratory Pressure (MEP >= 40 cmH2O), and pCO2 to direct extubation to NIPPV vs weaning hold.
"""

from typing import Dict


class MyasthenicCrisisExtubationEngine:
    """Evaluates respiratory weaning parameters for extubation readiness in Myasthenic Crisis."""

    def evaluate_extubation_readiness(
        self,
        negative_inspiratory_force_cmH2O: float,  # e.g., -35 cmH2O (<= -30 is good)
        vital_capacity_mL_kg: float,  # >= 15 mL/kg is good
        maximum_expiratory_pressure_cmH2O: float = 45.0,  # >= 40 cmH2O is good
        arterial_pco2_mmHg: float = 38.0,  # <= 45 mmHg is good
    ) -> Dict[str, any]:
        nif_adequate = negative_inspiratory_force_cmH2O <= -30.0
        fvc_adequate = vital_capacity_mL_kg >= 15.0
        mep_adequate = maximum_expiratory_pressure_cmH2O >= 40.0
        pco2_normal = arterial_pco2_mmHg <= 45.0

        ready_for_extubation = nif_adequate and fvc_adequate and mep_adequate and pco2_normal

        recommendation = f"EXTUBATION NOT READY: NIF {negative_inspiratory_force_cmH2O} cmH2O, FVC {vital_capacity_mL_kg} mL/kg. Continue mechanical ventilation, PLEX/IVIG therapy, and daily respiratory parameter checks"
        if ready_for_extubation:
            recommendation = f"EXTUBATION READINESS MET (NIF {negative_inspiratory_force_cmH2O} cmH2O, FVC {vital_capacity_mL_kg} mL/kg, MEP {maximum_expiratory_pressure_cmH2O} cmH2O): Proceed with spontaneous breathing trial (SBT). Have BiPAP / NIPPV standing by post-extubation for immediate transition"

        return {
            "negative_inspiratory_force_cmH2O": negative_inspiratory_force_cmH2O,
            "vital_capacity_mL_kg": vital_capacity_mL_kg,
            "extubation_ready": ready_for_extubation,
            "post_extubation_plan": "IMMEDIATE_TRANSITION_TO_NIPPV_BIPAP" if ready_for_extubation else "CONTINUE_MECHANICAL_VENTILATION",
            "clinical_recommendation": recommendation,
            "status": "EVALUATION_COMPLETE",
        }


# Singleton engine instance
mg_extubation_engine = MyasthenicCrisisExtubationEngine()
