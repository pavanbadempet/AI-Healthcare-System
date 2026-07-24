"""
Ischemic Stroke ASPECTS (Alberta Stroke Program Early CT Score) Evaluator
========================================================================
Evaluates early ischemic changes across 10 MCA territory regions on head CT
to guide endovascular thrombectomy (EVT) indications.
"""

from typing import Dict, List


class StrokeAspectsEvaluator:
    """Evaluates ASPECTS score (0 to 10) for acute ischemic stroke."""

    def evaluate_aspects_score(
        self,
        subcortical_hypodensity_regions: List[str],  # Caudate, Lentiform, Internal Capsule, Insular ribbon
        cortical_hypodensity_regions: List[str],     # M1, M2, M3, M4, M5, M6
    ) -> Dict[str, any]:
        deducted_regions = set(subcortical_hypodensity_regions + cortical_hypodensity_regions)
        aspects_score = max(0, 10 - len(deducted_regions))

        thrombectomy_eligible = aspects_score >= 6
        urgency = "STAT_NEUROINTERVENTIONAL_THROMBECTOMY" if thrombectomy_eligible else "NEUROLOGY_ICU_CONSERVATIVE"

        recommendation = "ASPECTS < 6: High risk of hemorrhagic transformation; conservative medical management"
        if aspects_score >= 6:
            recommendation = "ASPECTS >= 6: Stat Endovascular Thrombectomy (EVT) eligible for Large Vessel Occlusion (LVO)"

        return {
            "aspects_score": aspects_score,
            "hypodense_regions_count": len(deducted_regions),
            "endovascular_thrombectomy_eligible": thrombectomy_eligible,
            "urgency_level": urgency,
            "clinical_recommendation": recommendation,
            "status": "EVALUATION_COMPLETE",
        }


# Singleton evaluator instance
stroke_aspects_evaluator = StrokeAspectsEvaluator()
