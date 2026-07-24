"""
Unit tests for PERC Rule Engine
"""

from backend.ml.perc_rule_engine import perc_engine


def test_evaluate_perc_rule_negative():
    res = perc_engine.evaluate_perc_rule(
        age_50_or_older=False,
        heart_rate_100_or_higher=False,
        spo2_below_95_percent=False,
        unilateral_leg_swelling=False,
        hemoptysis=False,
        recent_trauma_or_surgery=False,
        prior_dvt_or_pe=False,
        estrogen_use=False,
    )
    assert res["perc_rule_negative"] is True
    assert res["pe_ruled_out_without_testing"] is True
    assert "safely ruled out" in res["recommendation"]


def test_evaluate_perc_rule_positive():
    res = perc_engine.evaluate_perc_rule(
        age_50_or_older=True,
        heart_rate_100_or_higher=False,
        spo2_below_95_percent=False,
        unilateral_leg_swelling=False,
        hemoptysis=False,
        recent_trauma_or_surgery=False,
        prior_dvt_or_pe=False,
        estrogen_use=False,
    )
    assert res["perc_rule_negative"] is False
    assert res["pe_ruled_out_without_testing"] is False
    assert "D-Dimer" in res["recommendation"]
