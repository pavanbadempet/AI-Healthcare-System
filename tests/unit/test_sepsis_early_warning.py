"""
Unit tests for Sepsis Early Warning Engine
"""

from backend.ml.sepsis_early_warning import sepsis_engine


def test_evaluate_sepsis_risk_low():
    res = sepsis_engine.evaluate_sepsis_risk(
        systolic_bp=120.0,
        respiratory_rate=16.0,
        altered_mental_status=False,
    )
    assert res["alert_level"] == "LOW_RISK"
    assert res["requires_stat_physician_notify"] is False


def test_evaluate_sepsis_risk_high():
    res = sepsis_engine.evaluate_sepsis_risk(
        systolic_bp=95.0,
        respiratory_rate=24.0,
        altered_mental_status=True,
        temperature_celsius=38.5,
        heart_rate=110.0,
        wbc_count=14.0,
    )
    assert res["qsofa_score"] == 3
    assert res["sirs_score"] == 4
    assert res["alert_level"] == "HIGH_SEPSIS_RISK"
    assert res["requires_stat_physician_notify"] is True
