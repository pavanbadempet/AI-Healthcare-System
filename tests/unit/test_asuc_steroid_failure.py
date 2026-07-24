"""
Unit tests for ASUC Steroid Failure Engine
"""

from backend.ml.asuc_steroid_failure_engine import asuc_steroid_failure_engine


def test_evaluate_asuc_responsive():
    res = asuc_steroid_failure_engine.evaluate_day3_steroid_response(
        days_on_iv_hydrocortisone=3,
        bloody_stool_frequency_per_day=4,
        crp_mg_L=18.0,
    )
    assert res["travis_criteria_failed"] is False
    assert res["rescue_therapy_indicated"] is False
    assert "STEROID RESPONSE ADEQUATE" in res["clinical_recommendation"]


def test_evaluate_asuc_travis_failure_rescue_infliximab():
    res = asuc_steroid_failure_engine.evaluate_day3_steroid_response(
        days_on_iv_hydrocortisone=3,
        bloody_stool_frequency_per_day=9,
        crp_mg_L=58.0,
    )
    assert res["travis_criteria_failed"] is True
    assert res["rescue_therapy_indicated"] is True
    assert res["oxford_colectomy_risk_pct"] == 85.0
    assert "DAY 3 STEROID FAILURE IDENTIFIED" in res["clinical_recommendation"]
    assert "Infliximab" in res["clinical_recommendation"]
