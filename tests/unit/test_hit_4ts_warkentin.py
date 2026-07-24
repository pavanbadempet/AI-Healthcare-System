"""
Unit tests for HIT 4Ts Warkentin Engine
"""

from backend.ml.hit_4ts_warkentin_engine import hit_4ts_engine


def test_calculate_hit_4ts_score_high():
    res = hit_4ts_engine.calculate_hit_4ts_score(
        thrombocytopenia_score=2,
        timing_score=2,
        thrombosis_score=2,
        other_causes_score=1,
    )
    assert res["hit_4ts_total_score"] == 7
    assert res["probability_tier"] == "HIGH_PROBABILITY"
    assert res["discontinue_heparin_stat"] is True
    assert res["direct_thrombin_inhibitor_indicated"] is True


def test_calculate_hit_4ts_score_low():
    res = hit_4ts_engine.calculate_hit_4ts_score(
        thrombocytopenia_score=1,
        timing_score=0,
        thrombosis_score=0,
        other_causes_score=1,
    )
    assert res["hit_4ts_total_score"] == 2
    assert res["probability_tier"] == "LOW_PROBABILITY"
    assert res["discontinue_heparin_stat"] is False
