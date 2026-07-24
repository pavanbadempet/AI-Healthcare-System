"""
Unit tests for IIH Venous Sinus Stenting Engine
"""

from backend.ml.iih_venous_sinus_stenting_engine import iih_stenting_engine


def test_evaluate_stenting_candidate():
    res = iih_stenting_engine.evaluate_stenting_candidacy(
        trans_stenotic_peak_pressure_gradient_mmHg=12.5,
        transverse_sinus_stenosis_on_mrv=True,
        lp_opening_pressure_mm_h2o=320.0,
        refractory_to_acetazolamide=True,
    )
    assert res["stenting_indicated"] is True
    assert res["significant_gradient"] is True
    assert "SELF_EXPANDING_NITINOL_VENOUS_STENT" in res["recommended_stent_type"]


def test_evaluate_stenting_insignificant_gradient():
    res = iih_stenting_engine.evaluate_stenting_candidacy(
        trans_stenotic_peak_pressure_gradient_mmHg=4.0,  # gradient < 8 mmHg
        transverse_sinus_stenosis_on_mrv=True,
        lp_opening_pressure_mm_h2o=280.0,
    )
    assert res["stenting_indicated"] is False
    assert res["significant_gradient"] is False
