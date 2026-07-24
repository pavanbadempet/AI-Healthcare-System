"""
Acute Kidney Injury RIFLE Criteria Engine
=========================================
Stages AKI using RIFLE criteria (Risk, Injury, Failure, Loss, ESRD) based on GFR decrease,
creatinine fold rise, and oliguria duration.
"""

from typing import Dict


class RifleAkiEngine:
    """Stages Acute Kidney Injury using RIFLE criteria."""

    def stage_rifle_aki(
        self,
        baseline_creatinine_mg_dL: float,
        current_creatinine_mg_dL: float,
        anuria_hours: float = 0.0,
        oliguria_less_than_0_5mL_kg_hr_hours: float = 0.0,
    ) -> Dict[str, any]:
        creatinine_ratio = round(current_creatinine_mg_dL / max(baseline_creatinine_mg_dL, 0.1), 2)

        rifle_category = "NO_AKI"
        recommendation = "Maintain hydration and standard renal function surveillance"

        if creatinine_ratio >= 3.0 or current_creatinine_mg_dL >= 4.0 or anuria_hours >= 12.0:
            rifle_category = "RIFLE_FAILURE"
            recommendation = "Urgent Nephrology Consult & evaluate hemodialysis / CRRT"
        elif creatinine_ratio >= 2.0 or oliguria_less_than_0_5mL_kg_hr_hours >= 12.0:
            rifle_category = "RIFLE_INJURY"
            recommendation = "Discontinue nephrotoxic medications & optimize renal perfusion"
        elif creatinine_ratio >= 1.5 or oliguria_less_than_0_5mL_kg_hr_hours >= 6.0:
            rifle_category = "RIFLE_RISK"
            recommendation = "Monitor fluid balance Q4H & repeat serum creatinine daily"

        return {
            "creatinine_fold_increase": creatinine_ratio,
            "rifle_category": rifle_category,
            "nephrology_consult_indicated": rifle_category == "RIFLE_FAILURE",
            "clinical_recommendation": recommendation,
            "status": "STAGING_COMPLETE",
        }


# Singleton engine instance
rifle_aki_engine = RifleAkiEngine()
