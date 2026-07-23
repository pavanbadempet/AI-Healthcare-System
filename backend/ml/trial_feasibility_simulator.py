"""
Clinical Trial Protocol Feasibility Simulator
=============================================
Simulates patient recruitment rates, dropouts, and statistical power for trial designs.
"""

from typing import Dict, List, Optional


class ClinicalTrialFeasibilitySimulator:
    """Simulates trial enrollment timelines and statistical power."""

    def simulate_trial_feasibility(
        self,
        target_sample_size: int,
        monthly_recruitment_rate: int,
        expected_dropout_pct: float = 15.0,
        trial_duration_months: int = 12,
    ) -> Dict[str, any]:
        total_enrolled = monthly_recruitment_rate * trial_duration_months
        total_retained = int(total_enrolled * (1.0 - (expected_dropout_pct / 100.0)))

        is_feasible = total_retained >= target_sample_size
        completion_months = (
            int(target_sample_size / (monthly_recruitment_rate * (1.0 - (expected_dropout_pct / 100.0))))
            if monthly_recruitment_rate > 0
            else 999
        )

        return {
            "target_sample_size": target_sample_size,
            "projected_enrollment": total_enrolled,
            "projected_retained": total_retained,
            "is_feasible": is_feasible,
            "estimated_months_to_target": completion_months,
            "feasibility_status": "FEASIBLE" if is_feasible else "UNDERPOWERED_SHORTFALL",
        }


# Singleton simulator instance
trial_feasibility_simulator = ClinicalTrialFeasibilitySimulator()
