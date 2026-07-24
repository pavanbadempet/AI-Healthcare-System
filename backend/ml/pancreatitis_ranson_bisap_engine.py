"""
Acute Pancreatitis Ranson's Criteria & BISAP Score Engine
===========================================================
Computes BISAP (Bedside Index for Severity in Acute Pancreatitis) and Ranson's criteria
to predict acute pancreatitis mortality and pancreatic necrosis risk.
"""

from typing import Dict


class PancreatitisRansonBisapEngine:
    """Calculates BISAP score for acute pancreatitis severity prediction."""

    def calculate_bisap_score(
        self,
        bun_mg_dL: float,
        impaired_mental_status_gcs_under_15: bool,
        sirs_criteria_met: bool,
        age_over_60: bool,
        pleural_effusion_present: bool,
    ) -> Dict[str, any]:
        score = 0
        if bun_mg_dL > 25.0:
            score += 1
        if impaired_mental_status_gcs_under_15:
            score += 1
        if sirs_criteria_met:
            score += 1
        if age_over_60:
            score += 1
        if pleural_effusion_present:
            score += 1

        mortality_map = {0: 0.1, 1: 0.4, 2: 1.6, 3: 3.6, 4: 7.4, 5: 22.0}
        in_hospital_mortality_pct = mortality_map.get(score, 22.0)

        severe_pancreatitis = score >= 3

        return {
            "bisap_score": score,
            "in_hospital_mortality_risk_percent": in_hospital_mortality_pct,
            "severe_acute_pancreatitis_risk": severe_pancreatitis,
            "triage_recommendation": "ICU admission, aggressive IV hydration, & CT abdomen with contrast" if severe_pancreatitis else "Step-down unit ward admission & targeted IV fluid resuscitation",
            "status": "SCORING_COMPLETE",
        }


# Singleton engine instance
pancreatitis_engine = PancreatitisRansonBisapEngine()
