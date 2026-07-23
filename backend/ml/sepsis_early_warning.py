"""
Clinical Sepsis Early Warning System (qSOFA & SIRS) Engine
===========================================================
Computes qSOFA (quick Sequential Organ Failure Assessment) and SIRS (Systemic Inflammatory
Response Syndrome) risk scores from real-time patient vitals and WBC lab results.
"""

from typing import Dict, Optional


class SepsisEarlyWarningEngine:
    """Calculates qSOFA and SIRS sepsis risk scores for inpatient monitoring."""

    def evaluate_sepsis_risk(
        self,
        systolic_bp: float,
        respiratory_rate: float,
        altered_mental_status: bool = False,
        temperature_celsius: Optional[float] = 37.0,
        heart_rate: Optional[float] = 72.0,
        wbc_count: Optional[float] = 7.5,
    ) -> Dict[str, any]:
        # 1. qSOFA Calculation (0 - 3)
        qsofa_score = 0
        if systolic_bp <= 100.0:
            qsofa_score += 1
        if respiratory_rate >= 22.0:
            qsofa_score += 1
        if altered_mental_status:
            qsofa_score += 1

        # 2. SIRS Calculation (0 - 4)
        sirs_score = 0
        if temperature_celsius is not None and (temperature_celsius > 38.0 or temperature_celsius < 36.0):
            sirs_score += 1
        if heart_rate is not None and heart_rate > 90.0:
            sirs_score += 1
        if respiratory_rate >= 20.0:
            sirs_score += 1
        if wbc_count is not None and (wbc_count > 12.0 or wbc_count < 4.0):
            sirs_score += 1

        # Alert level determination
        if qsofa_score >= 2 or sirs_score >= 3:
            alert_level = "HIGH_SEPSIS_RISK"
            recommendation = "IMMEDIATE ACTION: Draw blood cultures, measure serum lactate, and initiate broad-spectrum IV antibiotics within 1 hour."
        elif qsofa_score == 1 or sirs_score == 2:
            alert_level = "MODERATE_RISK"
            recommendation = "Increase vital sign monitoring frequency to Q2H. Re-eval serum lactate."
        else:
            alert_level = "LOW_RISK"
            recommendation = "Routine inpatient monitoring."

        return {
            "qsofa_score": qsofa_score,
            "sirs_score": sirs_score,
            "alert_level": alert_level,
            "clinical_recommendation": recommendation,
            "requires_stat_physician_notify": alert_level == "HIGH_SEPSIS_RISK",
        }


# Singleton engine instance
sepsis_engine = SepsisEarlyWarningEngine()
