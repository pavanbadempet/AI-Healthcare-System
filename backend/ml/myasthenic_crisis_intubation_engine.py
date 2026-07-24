"""
Myasthenia Gravis Crisis & Intubation Decision Engine
======================================================
Evaluates Single-Breath Count (< 20), Forced Vital Capacity (FVC < 15 mL/kg or < 50% predicted),
Negative Inspiratory Force (NIF > -20 cm H2O), and Maximum Expiratory Pressure (MEP < 40 cm H2O)
to trigger ICU admission, emergent PLEX vs IVIG, and elective intubation prior to arrest.
"""

from typing import Dict


class MyasthenicCrisisIntubationEngine:
    """Evaluates Myasthenic Crisis severity and elective intubation criteria."""

    def evaluate_myasthenic_crisis(
        self,
        single_breath_count: int,
        forced_vital_capacity_mL_kg: float,
        negative_inspiratory_force_cm_H2O: float,  # e.g., -15 (weak) to -60 (normal)
        maximum_expiratory_pressure_cm_H2O: float,  # e.g., 30 (weak) to 100 (normal)
        bulbar_dysphagia_aspiration_risk: bool = False,
    ) -> Dict[str, any]:
        rule_of_20_30_40_triggered = (
            forced_vital_capacity_mL_kg < 20.0
            or abs(negative_inspiratory_force_cm_H2O) < 30.0
            or maximum_expiratory_pressure_cm_H2O < 40.0
        )

        intubation_indicated = (
            forced_vital_capacity_mL_kg < 15.0
            or abs(negative_inspiratory_force_cm_H2O) < 20.0
            or single_breath_count < 15
            or bulbar_dysphagia_aspiration_risk
        )

        crisis_present = rule_of_20_30_40_triggered or intubation_indicated

        rescue_immunotherapy = "PLASMA_EXCHANGE_PLEX_5_SESSIONS_OR_IVIG_2G_KG"
        discontinue_pyridostigmine = intubation_indicated  # avoid excessive airway secretions

        recommendation = "Stable neuromuscular pulmonary mechanics; continue oral Pyridostigmine & Maintenance Immunosuppression"
        if intubation_indicated:
            recommendation = f"IMMINENT MYASTHENIC CRISIS (FVC {forced_vital_capacity_mL_kg} mL/kg, NIF {negative_inspiratory_force_cm_H2O} cm H2O): Elective endotracheal intubation indicated in ICU; temporarily HOLD oral Pyridostigmine to avoid airway secretions; initiate {rescue_immunotherapy}"
        elif crisis_present:
            recommendation = f"IMPENDING MYASTHENIC CRISIS (Rule of 20/30/40 triggered): Admit to Neuro-ICU; monitor FVC/NIF Q4H; initiate {rescue_immunotherapy}"

        return {
            "single_breath_count": single_breath_count,
            "fvc_mL_kg": forced_vital_capacity_mL_kg,
            "nif_cm_H2O": negative_inspiratory_force_cm_H2O,
            "rule_of_20_30_40_triggered": rule_of_20_30_40_triggered,
            "intubation_indicated": intubation_indicated,
            "hold_pyridostigmine": discontinue_pyridostigmine,
            "rescue_immunotherapy": rescue_immunotherapy,
            "clinical_recommendation": recommendation,
            "status": "EVALUATION_COMPLETE",
        }


# Singleton engine instance
mg_crisis_engine = MyasthenicCrisisIntubationEngine()
