"""
High-Altitude Pulmonary Edema (HAPE) & Cerebral Edema (HACE) Risk Evaluator
=============================================================================
Calculates Lake Louise Score for Acute Mountain Sickness (AMS) and evaluates HAPE/HACE emergency protocols.
"""

from typing import Dict


class HapeHaceRiskEvaluator:
    """Evaluates Lake Louise score for high-altitude medical emergencies (HAPE/HACE)."""

    def evaluate_altitude_illness(
        self,
        headache_severity: int,        # 0 to 3
        gastrointestinal_nausea: int,  # 0 to 3
        fatigue_weakness: int,         # 0 to 3
        dizziness_lightheadedness: int,  # 0 to 3
        dyspnea_at_rest: bool = False,
        ataxia_staggering_gait: bool = False,
        confusion_altered_mental_state: bool = False,
    ) -> Dict[str, any]:
        lake_louise_score = headache_severity + gastrointestinal_nausea + fatigue_weakness + dizziness_lightheadedness

        hace_suspected = ataxia_staggering_gait or confusion_altered_mental_state
        hape_suspected = dyspnea_at_rest

        emergency_level = "ROUTINE_ACCLIMATIZATION"
        recommendation = "Continue gradual ascent & maintain hydration"

        if hace_suspected or (hape_suspected and lake_louise_score >= 6):
            emergency_level = "STAT_ALTITUDE_EMERGENCY"
            recommendation = "Immediate emergency descent (min 500-1000m), supplemental O2, Dexamethasone 8mg IV/PO, Nifedipine 30mg ER, & hyperbaric chamber"
        elif hape_suspected:
            emergency_level = "HAPE_HIGH_ALTITUDE_PULMONARY_EDEMA"
            recommendation = "Immediate descent, supplemental O2, & Nifedipine 30mg ER"
        elif lake_louise_score >= 3:
            emergency_level = "ACUTE_MOUNTAIN_SICKNESS"
            recommendation = "Halt ascent, rest at current altitude, & Acetazolamide 250mg BID"

        return {
            "lake_louise_score": lake_louise_score,
            "emergency_level": emergency_level,
            "hace_suspected": hace_suspected,
            "hape_suspected": hape_suspected,
            "immediate_descent_required": emergency_level in ["STAT_ALTITUDE_EMERGENCY", "HAPE_HIGH_ALTITUDE_PULMONARY_EDEMA"],
            "clinical_recommendation": recommendation,
            "status": "EVALUATION_COMPLETE",
        }


# Singleton evaluator instance
hape_hace_evaluator = HapeHaceRiskEvaluator()
