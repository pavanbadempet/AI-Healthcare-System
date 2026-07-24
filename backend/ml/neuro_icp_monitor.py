"""
Neuro-ICU Intracranial Pressure (ICP) & Cerebral Perfusion Monitor
====================================================================
Computes Cerebral Perfusion Pressure (CPP = MAP - ICP) and detects acute intracranial hypertension
and brain herniation risk from continuous invasive EVD monitoring lines.
"""

from typing import Dict


class NeuroIcpMonitor:
    """Monitors Neuro-ICU intracranial pressure and cerebral perfusion safety."""

    def evaluate_cerebral_perfusion(
        self,
        mean_arterial_pressure_mmHg: float,
        intracranial_pressure_mmHg: float,
        pupillary_reactivity_intact: bool = True,
    ) -> Dict[str, any]:
        cpp = round(mean_arterial_pressure_mmHg - intracranial_pressure_mmHg, 1)

        herniation_risk = False
        status = "PERFUSION_ADEQUATE"

        if intracranial_pressure_mmHg > 22.0 or cpp < 60.0 or not pupillary_reactivity_intact:
            herniation_risk = True
            status = "CRITICAL_INTRACRANIAL_HYPERTENSION"

        return {
            "mean_arterial_pressure": mean_arterial_pressure_mmHg,
            "intracranial_pressure": intracranial_pressure_mmHg,
            "cerebral_perfusion_pressure": cpp,
            "herniation_risk": herniation_risk,
            "clinical_status": status,
            "recommended_intervention": "Stat Hypertonic Saline / Mannitol & Neurosurgery Consult" if herniation_risk else "Maintain CPP > 60 mmHg",
        }


# Singleton monitor instance
neuro_icp_monitor = NeuroIcpMonitor()
