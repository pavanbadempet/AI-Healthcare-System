"""
Unit tests for TTVR EVOQUE Sizing Engine
"""

from backend.ml.ttvr_evoque_sizing_engine import ttvr_engine


def test_evaluate_evoque_candidate():
    res = ttvr_engine.evaluate_ttvr_evoque_eligibility(
        tricuspid_annulus_perimeter_mm=124.0,
        tricuspid_annulus_area_cm2=11.5,
        ivc_diameter_mm=26.0,
        severe_tricuspid_regurgitation=True,
        anatomically_suitable_for_triclip=False,
    )
    assert res["ttvr_eligible"] is True
    assert res["recommended_evoque_size_mm"] == 48
    assert res["ttvr_phenotype"] == "EVOQUE_TTVR_CANDIDATE"


def test_evaluate_prefer_triclip():
    res = ttvr_engine.evaluate_ttvr_evoque_eligibility(
        tricuspid_annulus_perimeter_mm=110.0,
        tricuspid_annulus_area_cm2=9.0,
        ivc_diameter_mm=22.0,
        anatomically_suitable_for_triclip=True,
    )
    assert res["ttvr_eligible"] is False
    assert res["ttvr_phenotype"] == "PREFER_TRICLIP_TEER"
