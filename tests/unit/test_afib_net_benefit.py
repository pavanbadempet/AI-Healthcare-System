"""
Unit tests for AFib Net Benefit Evaluator
"""

from backend.ml.afib_net_benefit_evaluator import afib_net_benefit_evaluator


def test_evaluate_net_benefit_favorable():
    res = afib_net_benefit_evaluator.evaluate_net_benefit(
        stroke_risk_annual_pct=4.8,
        bleeding_risk_annual_pct=1.9,
        patient_age_years=70,
    )
    assert res["net_clinical_benefit_score"] > 0.0
    assert res["anticoagulation_net_favorable"] is True
    assert "favors DOAC" in res["clinical_decision_recommendation"]


def test_evaluate_net_benefit_unfavorable():
    res = afib_net_benefit_evaluator.evaluate_net_benefit(
        stroke_risk_annual_pct=0.6,
        bleeding_risk_annual_pct=8.7,
        patient_age_years=78,
    )
    assert res["net_clinical_benefit_score"] < 0.0
    assert res["anticoagulation_net_favorable"] is False
