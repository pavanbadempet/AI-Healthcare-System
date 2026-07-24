"""
Unit tests for Cambridge Chronic Pancreatitis Engine
"""

from backend.ml.cambridge_chronic_pancreatitis_engine import cambridge_pancreatitis_engine


def test_stage_cambridge_pancreatitis_severe():
    res = cambridge_pancreatitis_engine.stage_cambridge_pancreatitis(
        abnormal_side_branches_count=4,
        main_pancreatic_duct_dilated_over_3mm=True,
        intraductal_calcifications_present=True,
    )
    assert res["cambridge_stage"] == "SEVERE_CHRONIC_PANCREATITIS"
    assert res["pert_enzymes_indicated"] is True
    assert "PERT - Creon" in res["clinical_recommendation"]


def test_stage_cambridge_pancreatitis_normal():
    res = cambridge_pancreatitis_engine.stage_cambridge_pancreatitis(
        abnormal_side_branches_count=0,
    )
    assert res["cambridge_stage"] == "NORMAL"
    assert res["pert_enzymes_indicated"] is False
