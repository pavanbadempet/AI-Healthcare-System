"""
Multiple Sclerosis EDSS (Expanded Disability Status Scale) Engine
==================================================================
Calculates EDSS score (0.0 to 10.0) from Functional Systems scores and ambulation distance.
"""

from typing import Dict, Optional


class MsEdssCalculator:
    """Calculates Multiple Sclerosis EDSS disability score."""

    def calculate_edss_score(
        self,
        pyramidal_score: int,      # 0 to 6
        cerebellar_score: int,     # 0 to 5
        brainstem_score: int,      # 0 to 5
        sensory_score: int,        # 0 to 6
        bowel_bladder_score: int,  # 0 to 6
        visual_score: int,         # 0 to 6
        cerebral_score: int,       # 0 to 5
        ambulation_unassisted_meters: Optional[float] = None,
    ) -> Dict[str, any]:
        max_fs = max([
            pyramidal_score,
            cerebellar_score,
            brainstem_score,
            sensory_score,
            bowel_bladder_score,
            visual_score,
            cerebral_score,
        ])

        edss = 0.0

        if ambulation_unassisted_meters is not None and ambulation_unassisted_meters < 100:
            edss = 6.5
        elif ambulation_unassisted_meters is not None and ambulation_unassisted_meters < 300:
            edss = 6.0
        elif ambulation_unassisted_meters is not None and ambulation_unassisted_meters < 500:
            edss = 5.5
        elif max_fs >= 4:
            edss = 4.5
        elif max_fs >= 3:
            edss = 3.5
        elif max_fs >= 2:
            edss = 2.5
        elif max_fs >= 1:
            edss = 1.5

        disability_tier = "MILD_DISABILITY"
        if edss >= 6.0:
            disability_tier = "SEVERE_WALKING_IMPAIRMENT_REQUIRES_ASSISTANCE"
        elif edss >= 4.0:
            disability_tier = "MODERATE_DISABILITY_FULLY_AMBULATORY"

        return {
            "edss_score": edss,
            "disability_tier": disability_tier,
            "disease_modifying_therapy_indicated": True,
            "wheelchair_dependence_threshold_met": edss >= 7.0,
            "status": "SCORING_COMPLETE",
        }


# Singleton calculator instance
ms_edss_calculator = MsEdssCalculator()
