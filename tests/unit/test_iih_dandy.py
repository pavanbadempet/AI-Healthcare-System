"""
Unit tests for IIH Dandy Criteria Engine
"""

from backend.ml.iih_dandy_criteria_engine import iih_engine


def test_evaluate_iih_acetazolamide_candidate():
    res = iih_engine.evaluate_iih_dandy_criteria(
        lp_opening_pressure_mm_h2o=310.0,
        frisen_papilledema_grade=2,
        visual_field_mean_deviation_db=-3.5,
        csf_composition_normal=True,
    )
    assert res["dandy_criteria_met"] is True
    assert res["fulminant_iih_vision_threat"] is False
    assert "ACETAZOLAMIDE" in res["recommended_treatment"]


def test_evaluate_fulminant_iih_surgical():
    res = iih_engine.evaluate_iih_dandy_criteria(
        lp_opening_pressure_mm_h2o=380.0,
        frisen_papilledema_grade=5,
        visual_field_mean_deviation_db=-11.0,
        transverse_sinus_stenosis_present=True,
    )
    assert res["dandy_criteria_met"] is True
    assert res["fulminant_iih_vision_threat"] is True
    assert "TRANSVERSE_SINUS_STENTING" in res["recommended_treatment"]
