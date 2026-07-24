"""
Unit tests for Chronic HBV BMD Loss Engine
"""

from backend.ml.hepatitis_b_bmd_loss_engine import hbv_bmd_engine


def test_evaluate_bmd_osteoporosis():
    res = hbv_bmd_engine.evaluate_bmd_loss_management(
        lumbar_spine_t_score=-2.8,
        femoral_neck_t_score=-2.1,
    )
    assert res["bone_status"] == "OSTEOPOROSIS"
    assert res["bisphosphonate_indicated"] is True
    assert "ALENDRONATE" in res["recommended_bisphosphonate"]
    assert "BONE LOSS TREATMENT INDICATED" in res["clinical_recommendation"]


def test_evaluate_bmd_normal():
    res = hbv_bmd_engine.evaluate_bmd_loss_management(
        lumbar_spine_t_score=-0.4,
        femoral_neck_t_score=-0.2,
    )
    assert res["bone_status"] == "NORMAL_BMD"
    assert res["bisphosphonate_indicated"] is False
