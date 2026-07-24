"""
PAH Sotatercept (Winrevair) Activin Signaling Inhibitor Engine
==============================================================
Evaluates Sotatercept eligibility (WHO Group 1 PAH on background therapy), baseline hemoglobin (< 16 g/dL),
and platelet count (> 50,000/uL) to guide subcutaneous dosing (0.3 mg/kg to 0.7 mg/kg Q3W).
"""

from typing import Dict


class PahSotaterceptActivinEngine:
    """Evaluates Sotatercept-csaa (Activin signaling inhibitor) for pulmonary arterial hypertension."""

    def evaluate_sotatercept_eligibility(
        self,
        who_group_1_pah_confirmed: bool = True,
        on_background_era_pde5i_prostacyclin: bool = True,
        hemoglobin_g_dL: float = 14.0,  # Warning if > 16.0, hold if > 18.0
        platelet_count_per_uL: float = 180000.0,  # Hold if < 50,000
    ) -> Dict[str, any]:
        eligible = who_group_1_pah_confirmed and on_background_era_pde5i_prostacyclin
        safety_clearance = hemoglobin_g_dL < 16.0 and platelet_count_per_uL >= 50000.0

        sotatercept_indicated = eligible and safety_clearance

        starting_dose = "SOTATERCEPT_0.3_MG_KG_SUBQ_EVERY_3_WEEKS"
        target_dose = "SOTATERCEPT_0.7_MG_KG_SUBQ_EVERY_3_WEEKS"

        recommendation = "Sotatercept NOT indicated or temporarily held due to polycythemia (Hb >= 16 g/dL) or thrombocytopenia (platelets < 50k)"
        if sotatercept_indicated:
            recommendation = f"ELIGIBLE FOR SOTATERCEPT (Winrevair): Initiate {starting_dose} subQ, escalating to {target_dose} target dose. Monitor hemoglobin and platelets before each dose to prevent erythrocytosis and bleeding"

        return {
            "eligible": eligible,
            "safety_clearance": safety_clearance,
            "sotatercept_indicated": sotatercept_indicated,
            "recommended_starting_dose": starting_dose if sotatercept_indicated else "NONE",
            "clinical_recommendation": recommendation,
            "status": "EVALUATION_COMPLETE",
        }


# Singleton engine instance
sotatercept_engine = PahSotaterceptActivinEngine()
