"""
Unit tests for Acute Variceal Bleeding Baveno VII TIPS Engine
"""

from backend.ml.variceal_bleeding_baveno7_tips_engine import baveno7_tips_engine


def test_evaluate_baveno7_child_c_tips():
    res = baveno7_tips_engine.evaluate_baveno7_preemptive_tips(
        child_pugh_score_points=11,
        active_bleeding_on_endoscopy=True,
    )
    assert res["preemptive_tips_indicated"] is True
    assert res["recommended_timing_window"] == "WITHIN_24_TO_72_HOURS"
    assert "Baveno VII PRE-EMPTIVE TIPS INDICATED" in res["clinical_recommendation"]


def test_evaluate_baveno7_child_a_standard():
    res = baveno7_tips_engine.evaluate_baveno7_preemptive_tips(
        child_pugh_score_points=6,
    )
    assert res["preemptive_tips_indicated"] is False
