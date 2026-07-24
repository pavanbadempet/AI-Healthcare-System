"""
Generalized Myasthenia Gravis (gMG) Rozanolixizumab Dosing Engine
==================================================================
Evaluates weight-tiered subcutaneous Rozanolixizumab dosing (420 mg, 560 mg, 840 mg weekly for 6 weeks)
in AChR+ or MuSK+ gMG and checks total IgG trough levels (>= 200 mg/dL) before repeating treatment cycles.
"""

from typing import Dict


class GmgRozanolixizumabDosingEngine:
    """Evaluates weight-tiered Rozanolixizumab SC dosing and safety monitoring in gMG."""

    def evaluate_rozanolixizumab_dosing(
        self,
        patient_weight_kg: float,
        total_igg_level_mg_dL: float = 800.0,
        achr_or_musk_antibody_positive: bool = True,
        active_severe_infection: bool = False,
    ) -> Dict[str, any]:
        eligible = achr_or_musk_antibody_positive and not active_severe_infection and total_igg_level_mg_dL >= 200.0

        weekly_dose_mg = 560
        if patient_weight_kg < 50.0:
            weekly_dose_mg = 420
        elif patient_weight_kg >= 100.0:
            weekly_dose_mg = 840

        recommendation = "Rozanolixizumab NOT indicated (Requires AChR+ or MuSK+ antibody status, absence of severe infection, and Total IgG >= 200 mg/dL)"
        if eligible:
            recommendation = f"ELIGIBLE FOR ROZANOLIXIZUMAB: Administer Rozanolixizumab {weekly_dose_mg} mg SC once weekly for 6 weeks (Cycle 1). Re-evaluate MG-ADL score and confirm Total IgG >= 200 mg/dL prior to initiating subsequent 6-week cycles"

        return {
            "eligible_for_rozanolixizumab": eligible,
            "patient_weight_kg": patient_weight_kg,
            "weekly_dose_mg": weekly_dose_mg if eligible else 0,
            "treatment_cycle": "ONCE_WEEKLY_FOR_6_WEEKS",
            "total_igg_level_mg_dL": total_igg_level_mg_dL,
            "clinical_recommendation": recommendation,
            "status": "EVALUATION_COMPLETE",
        }


# Singleton engine instance
rozanolixizumab_engine = GmgRozanolixizumabDosingEngine()
