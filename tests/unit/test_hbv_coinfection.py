"""
Unit tests for Chronic HBV Co-Infection Management Engine
"""

from backend.ml.hbv_coinfection_management_engine import hbv_coinfection_engine


def test_evaluate_hbv_hiv_coinfection():
    res = hbv_coinfection_engine.evaluate_coinfection_strategy(
        hbsag_positive=True,
        hiv_coinfected=True,
    )
    assert res["hiv_coinfected"] is True
    assert "TENOFVIR" in res["art_backbone_recommendation"]
    assert "HBV/HIV CO-INFECTION" in res["clinical_recommendation"]


def test_evaluate_hbv_hcv_daa_reactivation_warning():
    res = hbv_coinfection_engine.evaluate_coinfection_strategy(
        hbsag_positive=True,
        hcv_coinfected=True,
        undergoing_hcv_daa_therapy=True,
    )
    assert res["hbv_reactivation_warning"] is True
    assert "HIGH RISK FOR HBV REACTIVATION FLARE" in res["clinical_recommendation"]
