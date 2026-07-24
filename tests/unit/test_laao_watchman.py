"""
Unit tests for LAAO Watchman Sizing Engine
"""

from backend.ml.laao_watchman_sizing_engine import laao_engine


def test_calculate_laao_device_size_candidate():
    res = laao_engine.calculate_laao_device_size(
        laa_landing_zone_max_diameter_mm=23.0,
        laa_landing_zone_min_diameter_mm=21.0,
        laa_usable_depth_mm=18.0,
        anatomy_type="WINDSOCK",
    )
    assert res["laao_indicated"] is True
    assert res["recommended_watchman_flx_size_mm"] == 24
    assert res["laao_phenotype"] == "LAAO_WATCHMAN_FLX_CANDIDATE"
    assert "Watchman FLX LAAO" in res["clinical_recommendation"]


def test_calculate_laao_device_size_oversized():
    res = laao_engine.calculate_laao_device_size(
        laa_landing_zone_max_diameter_mm=34.0,
        laa_landing_zone_min_diameter_mm=32.0,
        laa_usable_depth_mm=22.0,
    )
    assert res["laao_indicated"] is False
    assert res["laao_phenotype"] == "EXTRA_LARGE_LAA_LANDING_ZONE"
