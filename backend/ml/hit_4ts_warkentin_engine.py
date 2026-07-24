"""
Heparin-Induced Thrombocytopenia (HIT) Warkentin 4Ts Engine
============================================================
Scores 4Ts (Thrombocytopenia, Timing, Thrombosis, oTher causes) for HIT probability stratification.
"""

from typing import Dict


class Hit4tsWarkentinEngine:
    """Scores Warkentin 4Ts for Heparin-Induced Thrombocytopenia risk."""

    def calculate_hit_4ts_score(
        self,
        thrombocytopenia_score: int,  # 0, 1, or 2
        timing_score: int,            # 0, 1, or 2
        thrombosis_score: int,          # 0, 1, or 2
        other_causes_score: int,      # 0, 1, or 2
    ) -> Dict[str, any]:
        total_score = thrombocytopenia_score + timing_score + thrombosis_score + other_causes_score

        probability_tier = "LOW_PROBABILITY"
        stop_heparin = False
        non_heparin_anticoagulation = False

        if total_score >= 6:
            probability_tier = "HIGH_PROBABILITY"
            stop_heparin = True
            non_heparin_anticoagulation = True
        elif total_score >= 4:
            probability_tier = "INTERMEDIATE_PROBABILITY"
            stop_heparin = True
            non_heparin_anticoagulation = True

        recommendation = "Low HIT probability (<5%); safe to continue Heparin if clinically indicated"
        if stop_heparin:
            recommendation = "High/Intermediate HIT probability; Discontinue all Heparin products stat, order PF4-heparin immunoassay, & initiate Argatroban/Bivalirudin"

        return {
            "hit_4ts_total_score": total_score,
            "probability_tier": probability_tier,
            "discontinue_heparin_stat": stop_heparin,
            "direct_thrombin_inhibitor_indicated": non_heparin_anticoagulation,
            "clinical_recommendation": recommendation,
            "status": "SCORING_COMPLETE",
        }


# Singleton engine instance
hit_4ts_engine = Hit4tsWarkentinEngine()
