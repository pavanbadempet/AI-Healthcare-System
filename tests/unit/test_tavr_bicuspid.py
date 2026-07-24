"""
Unit tests for TAVR Bicuspid Aortic Valve Engine
"""

from backend.ml.tavr_bicuspid_aortic_valve_engine import bav_tavr_engine


def test_evaluate_bav_sapien3_candidate():
    res = bav_tavr_engine.evaluate_bav_tavr_sizing(
        annulus_area_mm2=480.0,
        intercommissural_distance_4mm_mm=26.0,
        sievers_type="TYPE_1_LR",
        heavy_raphe_calcification=False,
    )
    assert res["recommended_valve_family"] == "BALLOON_EXPANDABLE_SAPIEN_3"
    assert res["recommended_size_mm"] == 26


def test_evaluate_bav_evolut_heavy_calcification():
    res = bav_tavr_engine.evaluate_bav_tavr_sizing(
        annulus_area_mm2=490.0,
        intercommissural_distance_4mm_mm=21.0,
        sievers_type="TYPE_1_LR",
        heavy_raphe_calcification=True,
    )
    assert res["recommended_valve_family"] == "SELF_EXPANDING_EVOLUT_PRO_PLUS"
    assert res["recommended_size_mm"] == 29
