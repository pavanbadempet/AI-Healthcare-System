"""
Chronic Pancreatitis Functional Exocrine Insufficiency (PEI) Engine
====================================================================
Evaluates Fecal Elastase-1 (FE-1: < 100 ug/g severe PEI, 100-200 ug/g moderate PEI)
to optimize Pancreatic Enzyme Replacement Therapy (PERT) dosing and monitor fat-soluble vitamins (A, D, E, K).
"""

from typing import Dict, Optional


class PancreaticExocrineInsufficiencyEngine:
    """Evaluates Fecal Elastase-1 and PEI severity to guide PERT dosing."""

    def evaluate_pei_severity(
        self,
        fecal_elastase_1_ug_g: float,
        steatorrhea_diarrhea_present: bool = True,
        unintentional_weight_loss_kg: Optional[float] = None,
        vitamin_d_25_oh_ng_mL: Optional[float] = None,
    ) -> Dict[str, any]:
        pei_severity = "NORMAL_EXOCRINE_FUNCTION"
        pert_indicated = False
        pert_dose_units_per_meal = 0

        if fecal_elastase_1_ug_g < 100.0:
            pei_severity = "SEVERE_PANCREATIC_EXOCRINE_INSUFFICIENCY"
            pert_indicated = True
            pert_dose_units_per_meal = 75000
        elif fecal_elastase_1_ug_g <= 200.0:
            pei_severity = "MODERATE_PANCREATIC_EXOCRINE_INSUFFICIENCY"
            pert_indicated = True
            pert_dose_units_per_meal = 50000

        vitamin_d_deficient = vitamin_d_25_oh_ng_mL is not None and vitamin_d_25_oh_ng_mL < 20.0

        recommendation = "Normal Fecal Elastase-1 (> 200 ug/g): No evidence of exocrine insufficiency; consider alternative causes of malabsorption"
        if pei_severity == "SEVERE_PANCREATIC_EXOCRINE_INSUFFICIENCY":
            recommendation = "Severe PEI (FE-1 < 100 ug/g): Initiate PERT (75,000 USP lipase units per meal + 25,000-50,000 per snack with food); prescribe oral Fat-Soluble Vitamins (A, D, E, K)"
        elif pert_indicated:
            recommendation = "Moderate PEI (FE-1 100-200 ug/g): Initiate PERT (50,000 USP lipase units per meal); monitor 72-hour fecal fat & nutritional parameters"

        return {
            "fecal_elastase_1_ug_g": fecal_elastase_1_ug_g,
            "pei_severity": pei_severity,
            "pert_indicated": pert_indicated,
            "recommended_lipase_units_per_meal": pert_dose_units_per_meal,
            "vitamin_d_deficient": vitamin_d_deficient,
            "clinical_recommendation": recommendation,
            "status": "EVALUATION_COMPLETE",
        }


# Singleton engine instance
pei_engine = PancreaticExocrineInsufficiencyEngine()
