"""
30-Day Hospital Readmission Risk Engine
========================================
Calculates 30-day hospital readmission risk probabilities based on the LACE index
(Length of stay, Acuity of admission, Comorbidities Charlson Index, Emergency dept visits)
and vital sign trend volatility.
"""

from typing import Dict, List, Optional


class ReadmissionRiskEngine:
    """Computes 30-day post-discharge hospital readmission probabilities."""

    def calculate_readmission_risk(
        self,
        length_of_stay_days: int,
        is_acute_admission: bool,
        charlson_comorbidity_index: int,
        emergency_visits_past_6m: int,
        systolic_bp: Optional[float] = 120.0,
        heart_rate: Optional[float] = 72.0,
    ) -> Dict[str, any]:
        # 1. Compute LACE Index Score (0 - 19)
        l_score = min(length_of_stay_days, 7) if length_of_stay_days < 14 else 7
        a_score = 3 if is_acute_admission else 0
        c_score = min(charlson_comorbidity_index, 6)
        e_score = min(emergency_visits_past_6m, 4)

        lace_score = l_score + a_score + c_score + e_score

        # 2. Vital signs volatility penalty
        vital_penalty = 0
        if systolic_bp and (systolic_bp > 160 or systolic_bp < 90):
            vital_penalty += 2
        if heart_rate and (heart_rate > 100 or heart_rate < 50):
            vital_penalty += 2

        total_score = lace_score + vital_penalty

        # Sigmoid probability mapping
        readmission_probability = round(min(0.95, max(0.05, 1.0 / (1.0 + pow(2.718, -(total_score - 10) * 0.25)))), 3)

        if total_score >= 11:
            risk_tier = "HIGH"
            recommendation = "Schedule high-priority home nurse visit within 48h and follow-up call."
        elif total_score >= 7:
            risk_tier = "MODERATE"
            recommendation = "Schedule clinic follow-up appointment within 7 days."
        else:
            risk_tier = "LOW"
            recommendation = "Standard post-discharge care instructions and 14-day check-in."

        return {
            "lace_score": lace_score,
            "vital_volatility_penalty": vital_penalty,
            "total_risk_score": total_score,
            "readmission_probability": readmission_probability,
            "risk_tier": risk_tier,
            "clinical_recommendation": recommendation,
        }


# Singleton engine instance
readmission_engine = ReadmissionRiskEngine()
