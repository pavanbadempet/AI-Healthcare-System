"""
Unit tests for TTVI Anatomical Feasibility Engine
"""

from backend.ml.ttvi_anatomical_feasibility_engine import ttvi_engine


def test_evaluate_tricvalve_eligible():
    res = ttvi_engine.evaluate_bicaval_ttvi_suitability(
        ivc_diameter_mm=26.0,
        svc_diameter_mm=22.0,
        severe_torrential_tr_present=True,
        teer_and_evoque_ineligible=True,
    )
    assert res["bicaval_ttvi_suitable"] is True
    assert res["recommended_system"] == "TRICVALVE_BICAVAL_DUAL_STENT_SYSTEM"
    assert "ELIGIBLE FOR TRICVALVE" in res["clinical_recommendation"]


def test_evaluate_tricvalve_ineligible_ivc():
    res = ttvi_engine.evaluate_bicaval_ttvi_suitability(
        ivc_diameter_mm=38.0,  # Too large
        svc_diameter_mm=22.0,
    )
    assert res["bicaval_ttvi_suitable"] is False
