"""
Chronic Hepatitis B Tenofovir (TDF/TAF) Bone Mineral Density Loss Engine
========================================================================
Evaluates DXA scan T-score, annual percentage BMD loss, and osteopenia/osteoporosis
to recommend calcium + vitamin D3 and bisphosphonates (Alendronate/Zoledronic acid).
"""

from typing import Dict


class HepatitisBBmdLossEngine:
    """Evaluates bone mineral density loss management in Chronic HBV patients."""

    def evaluate_bmd_loss_management(
        self,
        lumbar_spine_t_score: float,
        femoral_neck_t_score: float,
        annual_bmd_decline_percent: float = 2.0,
        history_of_fragility_fracture: bool = False,
    ) -> Dict[str, any]:
        lowest_t_score = min(lumbar_spine_t_score, femoral_neck_t_score)

        bone_status = "NORMAL_BMD"
        if lowest_t_score <= -2.5 or history_of_fragility_fracture:
            bone_status = "OSTEOPOROSIS"
        elif lowest_t_score <= -1.0:
            bone_status = "OSTEOPENIA"

        bisphosphonate_indicated = bone_status == "OSTEOPOROSIS" or (
            bone_status == "OSTEOPENIA" and annual_bmd_decline_percent >= 5.0
        )

        recommendation = f"Bone status {bone_status} (T-score {lowest_t_score}): Routine calcium (1000 mg/day) + Vitamin D3 (800-2000 IU/day) supplementation; repeat DXA in 2 years"
        if bisphosphonate_indicated:
            recommendation = f"BONE LOSS TREATMENT INDICATED ({bone_status}, T-score {lowest_t_score}): Initiate Alendronate 70 mg orally weekly (or IV Zoledronic acid 5 mg yearly) + Calcium 1200 mg/day + Vitamin D3 2000 IU/day. Switch antiviral from TDF to TAF or Entecavir"

        return {
            "lowest_t_score": lowest_t_score,
            "bone_status": bone_status,
            "bisphosphonate_indicated": bisphosphonate_indicated,
            "recommended_bisphosphonate": "ALENDRONATE_70MG_WEEKLY_OR_ZOLEDRONIC_ACID_5MG_YEARLY" if bisphosphonate_indicated else "NONE",
            "clinical_recommendation": recommendation,
            "status": "EVALUATION_COMPLETE",
        }


# Singleton engine instance
hbv_bmd_engine = HepatitisBBmdLossEngine()
