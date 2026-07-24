"""
PERC Rule (Pulmonary Embolism Rule-out Criteria) Engine
=========================================================
Evaluates 8 clinical criteria to safely rule out PE in low-risk patients without D-Dimer or CT imaging.
"""

from typing import Dict


class PercRuleEngine:
    """Evaluates PERC rule criteria to exclude PE without testing."""

    def evaluate_perc_rule(
        self,
        age_50_or_older: bool,
        heart_rate_100_or_higher: bool,
        spo2_below_95_percent: bool,
        unilateral_leg_swelling: bool,
        hemoptysis: bool,
        recent_trauma_or_surgery: bool,
        prior_dvt_or_pe: bool,
        estrogen_use: bool,
    ) -> Dict[str, any]:
        criteria_met = [
            age_50_or_older,
            heart_rate_100_or_higher,
            spo2_below_95_percent,
            unilateral_leg_swelling,
            hemoptysis,
            recent_trauma_or_surgery,
            prior_dvt_or_pe,
            estrogen_use,
        ]

        positive_criteria_count = sum(1 for c in criteria_met if c)
        perc_negative = positive_criteria_count == 0

        return {
            "perc_positive_criteria_count": positive_criteria_count,
            "perc_rule_negative": perc_negative,
            "pe_ruled_out_without_testing": perc_negative,
            "recommendation": "PE safely ruled out without D-Dimer or CT imaging (<1.5% PE risk)" if perc_negative else "Order high-sensitivity D-Dimer assay",
            "status": "EVALUATION_COMPLETE",
        }


# Singleton engine instance
perc_engine = PercRuleEngine()
