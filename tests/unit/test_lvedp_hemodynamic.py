"""
Unit tests for LVEDP Hemodynamic Engine
"""

from backend.ml.lvedp_hemodynamic_engine import lvedp_engine


def test_evaluate_lvedp_hemodynamics_hfpef():
    res = lvedp_engine.evaluate_lvedp_hemodynamics(
        lvedp_mmHg=22.0,
        pcwp_mmHg=18.0,
        mean_pap_mmHg=32.0,
        pulmonary_vascular_resistance_wood_units=1.8,
    )
    assert res["elevated_filling_pressures"] is True
    assert res["hemodynamic_classification"] == "POSTCAPILLARY_HFPEF_LEFT_HEART_DISEASE"
    assert res["sglt2i_and_diuretics_indicated"] is True
    assert "SGLT2 inhibitor" in res["clinical_recommendation"]


def test_evaluate_lvedp_hemodynamics_normal():
    res = lvedp_engine.evaluate_lvedp_hemodynamics(
        lvedp_mmHg=12.0,
        pcwp_mmHg=10.0,
        mean_pap_mmHg=16.0,
    )
    assert res["elevated_filling_pressures"] is False
    assert res["hemodynamic_classification"] == "NORMAL_LEFT_HEART_FILLING_PRESSURES"
