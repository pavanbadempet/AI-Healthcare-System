"""
Unit tests for PASCAL Tricuspid TEER Engine
"""

from backend.ml.pascal_tricuspid_teer_engine import pascal_engine


def test_evaluate_pascal_candidate():
    res = pascal_engine.evaluate_pascal_eligibility(
        coaptation_gap_mm=5.5,
        septal_leaflet_length_mm=10.0,
        tricuspid_regurgitation_severity="SEVERE",
    )
    assert res["pascal_eligible"] is True
    assert res["recommended_device"] == "PASCAL_PRECISION_SPACER_IMPLANT"


def test_evaluate_pascal_ineligible_gap():
    res = pascal_engine.evaluate_pascal_eligibility(
        coaptation_gap_mm=9.5,  # gap > 7mm
        septal_leaflet_length_mm=10.0,
    )
    assert res["pascal_eligible"] is False
    assert res["recommended_device"] == "INELIGIBLE"
