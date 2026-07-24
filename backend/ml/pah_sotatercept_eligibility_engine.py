"""
Pulmonary Arterial Hypertension (PAH) Sotatercept Eligibility Engine
=====================================================================
Evaluates STELLAR trial criteria for Sotatercept (subcutaneous Activin signaling inhibitor):
WHO Group 1 PAH, background dual/triple therapy, PVR >= 5 Wood units, and Hb/platelet safety rules.
"""

from typing import Dict


class PahSotaterceptEligibilityEngine:
    """Evaluates Sotatercept eligibility and dosing safety for PAH."""

    def evaluate_sotatercept_eligibility(
        self,
        who_group: int,  # 1 = PAH, 2-5 = non-PAH
        pulmonary_vascular_resistance_wood_units: float,
        who_functional_class: int,  # 2, 3, 4
        on_background_dual_or_triple_pah_therapy: bool = True,
        hemoglobin_g_dL: float = 14.0,  # Warning if > 16 g/dL
        platelet_count_per_uL: float = 200000.0,  # Contraindicated if < 50,000
        patient_weight_kg: float = 70.0,
    ) -> Dict[str, any]:
        eligible = (
            who_group == 1
            and pulmonary_vascular_resistance_wood_units >= 5.0
            and who_functional_class in [2, 3]
            and on_background_dual_or_triple_pah_therapy
            and platelet_count_per_uL >= 50000.0
            and hemoglobin_g_dL <= 16.0
        )

        initial_dose_mg = round(0.3 * patient_weight_kg, 1)
        target_maintenance_dose_mg = round(0.7 * patient_weight_kg, 1)

        recommendation = "Sotatercept NOT indicated (Must be WHO Group 1 PAH with PVR >= 5 Wood units, FC II-III, on background therapy, Hb <= 16 g/dL, and Platelets >= 50,000/uL)"
        if eligible:
            recommendation = f"ELIGIBLE FOR SOTATERCEPT (STELLAR Criteria): Initiate 0.3 mg/kg SC ({initial_dose_mg} mg) Q3W for 1 dose, then titrate to target maintenance 0.7 mg/kg SC ({target_maintenance_dose_mg} mg) Q3W. Recheck Hb and platelets prior to each dose"

        return {
            "eligible_for_sotatercept": eligible,
            "initial_dose_mg": initial_dose_mg if eligible else 0.0,
            "target_maintenance_dose_mg": target_maintenance_dose_mg if eligible else 0.0,
            "dosing_frequency": "EVERY_3_WEEKS_SUBCUTANEOUS",
            "clinical_recommendation": recommendation,
            "status": "EVALUATION_COMPLETE",
        }


# Singleton engine instance
sotatercept_engine = PahSotaterceptEligibilityEngine()
