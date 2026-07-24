"""
Unit tests for RIFLE AKI Engine
"""

from backend.ml.rifle_aki_engine import rifle_aki_engine


def test_stage_rifle_aki_failure():
    res = rifle_aki_engine.stage_rifle_aki(
        baseline_creatinine_mg_dL=1.0,
        current_creatinine_mg_dL=3.5,
        anuria_hours=14.0,
    )
    assert res["rifle_category"] == "RIFLE_FAILURE"
    assert res["nephrology_consult_indicated"] is True
    assert "Nephrology Consult" in res["clinical_recommendation"]


def test_stage_rifle_aki_no_aki():
    res = rifle_aki_engine.stage_rifle_aki(
        baseline_creatinine_mg_dL=0.9,
        current_creatinine_mg_dL=0.95,
    )
    assert res["rifle_category"] == "NO_AKI"
    assert res["nephrology_consult_indicated"] is False
