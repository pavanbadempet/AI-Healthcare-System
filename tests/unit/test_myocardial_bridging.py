"""
Unit tests for Myocardial Bridging Index Engine
"""

from backend.ml.myocardial_bridging_index_engine import myocardial_bridging_engine


def test_evaluate_myocardial_bridging_surgery():
    res = myocardial_bridging_engine.evaluate_myocardial_bridging(
        systolic_diameter_compression_percent=75.0,
        diastolic_ffr_hyperemic=0.68,
        dobutamine_provocation_st_shift=True,
        ivus_half_moon_sign_present=True,
    )
    assert res["hemodynamically_significant"] is True
    assert res["bridging_phenotype"] == "HEMODYNAMICALLY_SIGNIFICANT_MYOCARDIAL_BRIDGING"
    assert res["surgical_unroofing_myotomy_indicated"] is True
    assert res["avoid_nitrates_and_stents"] is True
    assert "Surgical Unroofing" in res["clinical_recommendation"]


def test_evaluate_myocardial_bridging_benign():
    res = myocardial_bridging_engine.evaluate_myocardial_bridging(
        systolic_diameter_compression_percent=20.0,
        diastolic_ffr_hyperemic=0.92,
    )
    assert res["hemodynamically_significant"] is False
    assert res["bridging_phenotype"] == "NON_SIGNIFICANT_BRIDGING"
    assert res["surgical_unroofing_myotomy_indicated"] is False
