"""
Unit tests for Hemodynamic Instability Predictor
"""

from backend.ml.hemodynamic_instability_model import hemodynamic_model


def test_predict_instability_risk_high():
    res = hemodynamic_model.predict_instability_risk(
        mean_arterial_pressure_mmHg=60.0,
        pulse_pressure_variation_percent=16.0,
        heart_rate_bpm=115,
        lactate_mmol_L=3.1,
    )
    assert res["high_instability_risk"] is True
    assert res["instability_risk_score"] >= 0.50
    assert "IV fluid bolus" in res["recommended_action"]


def test_predict_instability_risk_low():
    res = hemodynamic_model.predict_instability_risk(
        mean_arterial_pressure_mmHg=82.0,
        pulse_pressure_variation_percent=8.0,
        heart_rate_bpm=72,
        lactate_mmol_L=1.1,
    )
    assert res["high_instability_risk"] is False
    assert res["instability_risk_score"] < 0.50
