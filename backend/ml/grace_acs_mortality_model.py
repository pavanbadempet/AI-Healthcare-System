"""
GRACE 2.0 Acute Coronary Syndrome (ACS) Mortality Predictor
============================================================
Calculates in-hospital and 6-month post-discharge mortality risk percentage for ACS
(STEMI & NSTEMI) based on clinical presentation and hemodynamics.
"""

from typing import Dict


class GraceAcsMortalityModel:
    """Calculates GRACE 2.0 risk score and mortality probability for ACS patients."""

    def calculate_grace_mortality(
        self,
        age_years: int,
        heart_rate_bpm: int,
        systolic_bp_mmHg: int,
        creatinine_mg_dL: float,
        killip_class: int,  # 1 to 4
        cardiac_arrest_at_admission: bool = False,
        st_segment_deviation: bool = True,
        elevated_cardiac_enzymes: bool = True,
    ) -> Dict[str, any]:
        score = 0
        if age_years >= 80:
            score += 100
        elif age_years >= 70:
            score += 75
        elif age_years >= 60:
            score += 50
        elif age_years >= 50:
            score += 30

        if heart_rate_bpm >= 110:
            score += 30
        elif heart_rate_bpm >= 90:
            score += 18

        if systolic_bp_mmHg < 100:
            score += 40
        elif systolic_bp_mmHg < 120:
            score += 24

        if creatinine_mg_dL >= 2.0:
            score += 28
        elif creatinine_mg_dL >= 1.4:
            score += 15

        score += (killip_class - 1) * 20

        if cardiac_arrest_at_admission:
            score += 39
        if st_segment_deviation:
            score += 28
        if elevated_cardiac_enzymes:
            score += 14

        inhospital_mortality_pct = round(min(score * 0.12, 50.0), 1)
        six_month_mortality_pct = round(min(score * 0.25, 75.0), 1)

        category = "LOW_RISK"
        if score >= 140:
            category = "HIGH_RISK"
        elif score >= 109:
            category = "INTERMEDIATE_RISK"

        return {
            "grace_score": score,
            "in_hospital_mortality_percent": inhospital_mortality_pct,
            "six_month_mortality_percent": six_month_mortality_pct,
            "risk_category": category,
            "urgent_coronary_angiography_indicated": score >= 140 or killip_class >= 3 or cardiac_arrest_at_admission,
            "status": "PREDICTION_COMPLETE",
        }


# Singleton model instance
grace_model = GraceAcsMortalityModel()
