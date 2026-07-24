"""
TIMI Risk Score for NSTEMI / Unstable Angina
=============================================
Calculates 14-day risk of all-cause mortality, recurrent MI, or urgent revascularization.
"""

from typing import Dict


class TimiNstemiScoreEngine:
    """Calculates TIMI risk score for NSTEMI / UA patients."""

    def calculate_timi_score(
        self,
        age_65_or_older: bool,
        three_or_more_cad_risk_factors: bool,
        known_cad_stenosis_50pct_or_more: bool,
        aspirin_use_past_7_days: bool,
        severe_angina_past_24h: bool,
        st_deviation_0_5mm_or_more: bool,
        elevated_cardiac_markers: bool,
    ) -> Dict[str, any]:
        score = 0
        if age_65_or_older:
            score += 1
        if three_or_more_cad_risk_factors:
            score += 1
        if known_cad_stenosis_50pct_or_more:
            score += 1
        if aspirin_use_past_7_days:
            score += 1
        if severe_angina_past_24h:
            score += 1
        if st_deviation_0_5mm_or_more:
            score += 1
        if elevated_cardiac_markers:
            score += 1

        risk_pct_map = {0: 4.7, 1: 4.7, 2: 8.3, 3: 13.2, 4: 19.9, 5: 26.2, 6: 40.9, 7: 40.9}
        estimated_risk_pct = risk_pct_map.get(score, 40.9)

        category = "LOW_RISK"
        recommendation = "Conservative medical management & outpatient stress testing"
        if score >= 5:
            category = "HIGH_RISK"
            recommendation = "Early invasive strategy (Coronary Angiography within 24h) + dual antiplatelet therapy"
        elif score >= 3:
            category = "INTERMEDIATE_RISK"
            recommendation = "Inpatient telemetry monitoring & consider early invasive strategy"

        return {
            "timi_score": score,
            "fourteen_day_composite_event_risk_percent": estimated_risk_pct,
            "risk_category": category,
            "clinical_recommendation": recommendation,
            "status": "CALCULATION_COMPLETE",
        }


# Singleton score engine instance
timi_engine = TimiNstemiScoreEngine()
