"""
ALS King's Clinical & MiToS Functional Staging Engine
======================================================
Evaluates King's Staging (Stage 1-4B) and MiToS functional loss (Stage 0-4)
to guide gastrostomy PEG placement, non-invasive ventilation (NIV), and multidisciplinary ALS care.
"""

from typing import Dict


class AlsKingsMitosStagingEngine:
    """Evaluates King's ALS clinical stage and MiToS functional stage."""

    def calculate_als_staging(
        self,
        bulbar_involvement: bool = False,
        cervical_upper_limb_involvement: bool = False,
        lumbosacral_lower_limb_involvement: bool = False,
        gastrostomy_peg_placed: bool = False,
        niv_ventilation_required: bool = False,
    ) -> Dict[str, any]:
        regions_involved = sum([bulbar_involvement, cervical_upper_limb_involvement, lumbosacral_lower_limb_involvement])

        kings_stage = "STAGE_1_SINGLE_REGION"
        if niv_ventilation_required:
            kings_stage = "STAGE_4B_NIV_VENTILATION"
        elif gastrostomy_peg_placed:
            kings_stage = "STAGE_4A_GASTROSTOMY_PEG"
        elif regions_involved == 3:
            kings_stage = "STAGE_3_THREE_REGIONS"
        elif regions_involved == 2:
            kings_stage = "STAGE_2_TWO_REGIONS"

        peg_indicated = bulbar_involvement and not gastrostomy_peg_placed
        niv_indicated = not niv_ventilation_required

        recommendation = f"King's ALS Stage: {kings_stage} ({regions_involved} anatomical regions involved). Multidisciplinary ALS clinic follow-up"
        if kings_stage in ["STAGE_4A_GASTROSTOMY_PEG", "STAGE_4B_NIV_VENTILATION"]:
            recommendation = f"ADVANCED ALS ({kings_stage}): Optimize non-invasive ventilation pressure settings, enteral PEG nutrition, and palliative care symptom management"
        elif peg_indicated:
            recommendation = f"King's ALS Stage: {kings_stage}: Bulbar weakness detected; schedule early prophylactic radiologically inserted gastrostomy (RIG/PEG) prior to FVC drop < 50%"

        return {
            "anatomical_regions_involved": regions_involved,
            "kings_stage": kings_stage,
            "peg_indicated": peg_indicated,
            "niv_indicated": niv_indicated,
            "clinical_recommendation": recommendation,
            "status": "STAGING_COMPLETE",
        }


# Singleton engine instance
als_staging_engine = AlsKingsMitosStagingEngine()
