"""
Unit tests for Tricuspid TriClip Engine
"""

from backend.ml.tricuspid_triclip_engine import triclip_engine


def test_evaluate_triclip_eligibility_optimal():
    res = triclip_engine.evaluate_triclip_eligibility(
        tricuspid_regurgitation_grade_1_to_5=4,  # Massive TR
        coaptation_gap_mm=4.5,
        septal_leaflet_length_mm=11.0,
        pulmonary_artery_systolic_pressure_pasp_mmHg=42.0,
    )
    assert res["triclip_teer_indicated"] is True
    assert res["anatomically_favorable"] is True
    assert res["tricuspid_repair_phenotype"] == "TRICLIP_TEER_OPTIMAL_CANDIDATE"
    assert "Optimal Candidate for TriClip TEER" in res["clinical_recommendation"]


def test_evaluate_triclip_eligibility_unfavorable():
    res = triclip_engine.evaluate_triclip_eligibility(
        tricuspid_regurgitation_grade_1_to_5=5,  # Torrential TR
        coaptation_gap_mm=9.5,                   # Gap > 7mm
        septal_leaflet_length_mm=8.0,
        pulmonary_artery_systolic_pressure_pasp_mmHg=68.0, # PASP > 60
    )
    assert res["triclip_teer_indicated"] is False
    assert res["anatomically_favorable"] is False
    assert res["tricuspid_repair_phenotype"] == "UNFAVORABLE_TRICUSPID_ANATOMY_SEVERE_PHTN_OR_GAP"
