"""
Heparin-Induced Thrombocytopenia (HIT) 4Ts Scoring Engine
==========================================================
Computes pre-test probability score for Heparin-Induced Thrombocytopenia
(Thrombocytopenia, Timing, Thrombosis, oTher causes) to guide non-heparin anticoagulation switch.
"""

from typing import Dict


class Hit4TsScoreEngine:
    """Calculates pre-test probability 4Ts score for HIT."""

    def calculate_hit_4ts_score(
        self,
        thrombocytopenia_points: int,  # 0, 1, or 2
        timing_points: int,            # 0, 1, or 2
        thrombosis_points: int,          # 0, 1, or 2
        other_cause_points: int,       # 0, 1, or 2
    ) -> Dict[str, any]:
        total_score = thrombocytopenia_points + timing_points + thrombosis_points + other_cause_points

        probability = "LOW_PROBABILITY"
        recommendation = "Continue heparin monitoring; low probability of HIT (<1%)"

        if total_score >= 6:
            probability = "HIGH_PROBABILITY"
            recommendation = "Discontinue all heparin; start non-heparin anticoagulant (Argatroban/Fondaparinux) & order anti-PF4 ELISA"
        elif total_score >= 4:
            probability = "INTERMEDIATE_PROBABILITY"
            recommendation = "Discontinue heparin & order anti-PF4 antibody testing"

        return {
            "total_4ts_score": total_score,
            "pretest_probability_category": probability,
            "clinical_recommendation": recommendation,
            "discontinue_heparin_immediately": total_score >= 4,
            "status": "SCORING_COMPLETE",
        }


# Singleton engine instance
hit_4ts_engine = Hit4TsScoreEngine()
