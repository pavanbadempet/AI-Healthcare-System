"""
Unit tests for MG Surgical Risk & Pre-Operative PLEX Clearance Engine
"""

from backend.ml.mg_preop_plex_clearance_engine import mg_preop_plex_engine


def test_evaluate_cleared_for_surgery():
    res = mg_preop_plex_engine.evaluate_preop_clearance(
        planned_procedure="THYMECTOMY",
        forced_vital_capacity_liters=3.2,
        fvc_percent_predicted=92.0,
        bulbar_symptoms_present=False,
        qmg_score=5.0,
    )
    assert res["plex_or_ivig_indicated"] is False
    assert "CLEARED FOR SURGERY" in res["clinical_recommendation"]


def test_evaluate_mandate_preop_plex():
    res = mg_preop_plex_engine.evaluate_preop_clearance(
        planned_procedure="THYMECTOMY",
        forced_vital_capacity_liters=1.7,
        fvc_percent_predicted=65.0,
        bulbar_symptoms_present=True,
        qmg_score=14.5,
    )
    assert res["plex_or_ivig_indicated"] is True
    assert res["high_respiratory_risk"] is True
    assert res["high_bulbar_risk"] is True
    assert "MANDATE pre-operative optimization" in res["clinical_recommendation"]
    assert "Plasma Exchange" in res["clinical_recommendation"]
