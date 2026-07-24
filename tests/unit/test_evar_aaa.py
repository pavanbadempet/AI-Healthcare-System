"""
Unit tests for EVAR AAA Anatomical Feasibility Engine
"""

from backend.ml.evar_aaa_anatomical_feasibility_engine import evar_engine


def test_evaluate_standard_evar_candidate():
    res = evar_engine.evaluate_evar_feasibility(
        aaa_max_sac_diameter_mm=58.0,
        proximal_neck_length_mm=15.0,
        proximal_neck_diameter_mm=24.0,
        proximal_neck_angulation_deg=35.0,
        min_iliac_access_diameter_mm=7.5,
    )
    assert res["repair_indicated"] is True
    assert res["standard_evar_eligible"] is True
    assert res["recommended_approach"] == "STANDARD_BIFURCATED_EVAR_STENT_GRAFT"


def test_evaluate_fevar_short_neck():
    res = evar_engine.evaluate_evar_feasibility(
        aaa_max_sac_diameter_mm=62.0,
        proximal_neck_length_mm=6.0,  # neck < 10mm
        proximal_neck_diameter_mm=26.0,
        proximal_neck_angulation_deg=40.0,
        min_iliac_access_diameter_mm=7.0,
    )
    assert res["repair_indicated"] is True
    assert res["standard_evar_eligible"] is False
    assert res["recommended_approach"] == "FENESTRATED_OR_BRANCHED_EVAR_FEVAR_BEVAR"
