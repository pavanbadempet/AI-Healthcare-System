"""
Unit tests for HIT 4Ts Scoring Engine
"""

from backend.ml.hit_4ts_score_engine import hit_4ts_engine


def test_calculate_hit_4ts_score_high():
    res = hit_4ts_engine.calculate_hit_4ts_score(
        thrombocytopenia_points=2,
        timing_points=2,
        thrombosis_points=2,
        other_cause_points=1,
    )
    assert res["total_4ts_score"] == 7
    assert res["pretest_probability_category"] == "HIGH_PROBABILITY"
    assert res["discontinue_heparin_immediately"] is True
    assert "Argatroban" in res["clinical_recommendation"]


def test_calculate_hit_4ts_score_low():
    res = hit_4ts_engine.calculate_hit_4ts_score(
        thrombocytopenia_points=1,
        timing_points=0,
        thrombosis_points=0,
        other_cause_points=1,
    )
    assert res["total_4ts_score"] == 2
    assert res["pretest_probability_category"] == "LOW_PROBABILITY"
    assert res["discontinue_heparin_immediately"] is False
