"""
Unit tests for Pancreatitis BISAP Engine
"""

from backend.ml.pancreatitis_ranson_bisap_engine import pancreatitis_engine


def test_calculate_bisap_score_severe():
    res = pancreatitis_engine.calculate_bisap_score(
        bun_mg_dL=30.0,
        impaired_mental_status_gcs_under_15=True,
        sirs_criteria_met=True,
        age_over_60=True,
        pleural_effusion_present=True,
    )
    assert res["bisap_score"] == 5
    assert res["severe_acute_pancreatitis_risk"] is True
    assert res["in_hospital_mortality_risk_percent"] == 22.0
    assert "ICU admission" in res["triage_recommendation"]


def test_calculate_bisap_score_mild():
    res = pancreatitis_engine.calculate_bisap_score(
        bun_mg_dL=16.0,
        impaired_mental_status_gcs_under_15=False,
        sirs_criteria_met=False,
        age_over_60=False,
        pleural_effusion_present=False,
    )
    assert res["bisap_score"] == 0
    assert res["severe_acute_pancreatitis_risk"] is False
