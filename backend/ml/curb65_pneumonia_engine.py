"""
CURB-65 Pneumonia Mortality & Inpatient Triage Engine
======================================================
Calculates CURB-65 score (Confusion, Uremia, Respiratory rate, Blood pressure, Age 65+)
to triage community-acquired pneumonia (Outpatient vs Inpatient vs ICU).
"""

from typing import Dict


class Curb65PneumoniaEngine:
    """Calculates CURB-65 score for pneumonia triage and 30-day mortality risk."""

    def calculate_curb65_score(
        self,
        confusion_present: bool,
        bun_mg_dL: float,
        respiratory_rate_bpm: int,
        systolic_bp_mmHg: int,
        diastolic_bp_mmHg: int,
        age_years: int,
    ) -> Dict[str, any]:
        score = 0
        if confusion_present:
            score += 1
        if bun_mg_dL > 19.0:
            score += 1
        if respiratory_rate_bpm >= 30:
            score += 1
        if systolic_bp_mmHg < 90 or diastolic_bp_mmHg <= 60:
            score += 1
        if age_years >= 65:
            score += 1

        mortality_map = {0: 0.6, 1: 2.7, 2: 6.8, 3: 14.0, 4: 27.8, 5: 27.8}
        thirty_day_mortality_pct = mortality_map.get(score, 27.8)

        triage_recommendation = "Outpatient treatment with oral antibiotics"
        if score >= 3:
            triage_recommendation = "Inpatient ICU admission for severe pneumonia"
        elif score == 2:
            triage_recommendation = "Inpatient hospital ward admission or close outpatient monitoring"

        return {
            "curb65_score": score,
            "thirty_day_mortality_risk_percent": thirty_day_mortality_pct,
            "triage_recommendation": triage_recommendation,
            "inpatient_admission_indicated": score >= 2,
            "icu_admission_indicated": score >= 3,
            "status": "TRIAGE_COMPLETE",
        }


# Singleton engine instance
curb65_engine = Curb65PneumoniaEngine()
