"""
Unit tests for TPVR Alterra Adaptive Prestent Engine
"""

from backend.ml.tpvr_alterra_adaptive_prestent_engine import alterra_engine


def test_evaluate_alterra_eligible():
    res = alterra_engine.evaluate_alterra_candidacy(
        native_rvot_diameter_mm=32.0,
        severe_pulmonary_regurgitation=True,
    )
    assert res["alterra_eligible"] is True
    assert "ALTERRA_ADAPTIVE_PRESTENT" in res["recommended_prestent"]
    assert "ELIGIBLE FOR ALTERRA ADAPTIVE PRESTENT" in res["clinical_recommendation"]


def test_evaluate_alterra_coronary_risk_contraindicated():
    res = alterra_engine.evaluate_alterra_candidacy(
        native_rvot_diameter_mm=32.0,
        coronary_compression_risk=True,
    )
    assert res["alterra_eligible"] is False
    assert res["reason"] == "CORONARY_COMPRESSION_RISK"
