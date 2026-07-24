"""
Unit tests for FIB-4 Calculator
"""

from backend.ml.fib4_nafld_fibrosis_calculator import fib4_calculator


def test_calculate_fib4_score_high():
    res = fib4_calculator.calculate_fib4_score(
        age_years=58,
        ast_u_l=95.0,
        alt_u_l=45.0,
        platelet_count_10_3_ul=110.0,
    )
    assert res["fib4_score"] > 2.67
    assert res["fibrosis_risk_tier"] == "HIGH_RISK_ADVANCED_FIBROSIS_F3_F4"
    assert res["transient_elastography_fibroscan_indicated"] is True
    assert "Hepatology referral" in res["clinical_recommendation"]


def test_calculate_fib4_score_low():
    res = fib4_calculator.calculate_fib4_score(
        age_years=35,
        ast_u_l=22.0,
        alt_u_l=25.0,
        platelet_count_10_3_ul=280.0,
    )
    assert res["fib4_score"] < 1.30
    assert res["fibrosis_risk_tier"] == "LOW_RISK_F0_F1"
    assert res["transient_elastography_fibroscan_indicated"] is False
