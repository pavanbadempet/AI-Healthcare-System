"""
Unit tests for Aortic Arch FET Thoraflex Engine
"""

from backend.ml.aortic_arch_fet_thoraflex_engine import fet_engine


def test_evaluate_fet_candidate():
    res = fet_engine.evaluate_fet_eligibility(
        arch_aneurysm_max_diameter_mm=58.0,
        descending_aorta_landing_diameter_mm=30.0,
        ishimaru_landing_zone=0,
    )
    assert res["fet_eligible"] is True
    assert res["recommended_fet_size_mm"] == 32
    assert "Thoraflex Hybrid" in res["clinical_recommendation"]


def test_evaluate_fet_dissection_candidate():
    res = fet_engine.evaluate_fet_eligibility(
        arch_aneurysm_max_diameter_mm=48.0,  # dissection threshold >= 50mm
        descending_aorta_landing_diameter_mm=26.0,
        acute_type_a_dissection=True,
    )
    assert res["fet_eligible"] is True
    assert res["recommended_fet_size_mm"] == 28
