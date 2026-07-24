"""
Chronic Pancreatitis M-ANNHEIM Staging Engine
============================================
Scores risk factors and stages chronic pancreatitis disease severity (Stage M0 to Stage M4).
"""

from typing import Dict


class MannheimChronicPancreatitisEngine:
    """Stages Chronic Pancreatitis severity using M-ANNHEIM classification."""

    def stage_mannheim_chronic_pancreatitis(
        self,
        alcohol_etiology: bool = False,
        nicotine_smoking: bool = False,
        hereditary_genetic_factors: bool = False,
        pancreatic_duct_stone_or_stricture: bool = False,
        exocrine_pancreatic_insufficiency: bool = False,
        endocrine_diabetes_mellitus: bool = False,
        persistent_intractable_pain: bool = False,
    ) -> Dict[str, any]:
        stage = "STAGE_M0_SUBCLINICAL"

        if persistent_intractable_pain and (exocrine_pancreatic_insufficiency or endocrine_diabetes_mellitus):
            stage = "STAGE_M4_ADVANCED_BURNT_OUT"
        elif pancreatic_duct_stone_or_stricture and persistent_intractable_pain:
            stage = "STAGE_M3_COMPLICATED_OBSTRUCTIVE"
        elif exocrine_pancreatic_insufficiency or endocrine_diabetes_mellitus:
            stage = "STAGE_M2_OVERT_INSUFFICIENCY"
        elif persistent_intractable_pain:
            stage = "STAGE_M1_EARLY_PAINFUL"

        endoscopic_or_surgical_intervention = stage in ["STAGE_M3_COMPLICATED_OBSTRUCTIVE", "STAGE_M4_ADVANCED_BURNT_OUT"]

        recommendation = "Lifestyle modification, PERT (Pancreatic Enzyme Replacement Therapy), & pain control"
        if stage == "STAGE_M3_COMPLICATED_OBSTRUCTIVE":
            recommendation = "ERCP Pancreatic Sphincterotomy + Duct Stenting OR Surgical Decompression (Frey / Puestow Procedure)"
        elif stage == "STAGE_M4_ADVANCED_BURNT_OUT":
            recommendation = "High-dose PERT (Creon 50k units/meal) + Insulin therapy & total pancreatectomy evaluation"

        return {
            "mannheim_stage": stage,
            "endoscopic_or_surgical_decompression_indicated": endoscopic_or_surgical_intervention,
            "clinical_recommendation": recommendation,
            "status": "STAGING_COMPLETE",
        }


# Singleton engine instance
mannheim_pancreatitis_engine = MannheimChronicPancreatitisEngine()
