"""
Unit tests for TPVR RVOT Anatomy Engine
"""

from backend.ml.tpvr_rvot_anatomy_engine import tpvr_anatomy_engine


def test_evaluate_tpvr_harmony_native_patched():
    res = tpvr_anatomy_engine.evaluate_tpvr_suitability(
        rvot_anatomy_type="NATIVE_PATCHED_RVOT",
        rvot_waist_diameter_mm=28.0,
        pulmonary_regurgitation_fraction_percent=42.0,
        rvedvi_mL_m2=165.0,
    )
    assert res["tpvr_indicated"] is True
    assert res["recommended_valve_system"] == "MEDTRONIC_HARMONY_TPVR_22MM_OR_25MM"
    assert "TPVR INDICATED" in res["clinical_recommendation"]


def test_evaluate_tpvr_melody_conduit():
    res = tpvr_anatomy_engine.evaluate_tpvr_suitability(
        rvot_anatomy_type="CONDUIT",
        rvot_waist_diameter_mm=20.0,
        pulmonary_regurgitation_fraction_percent=38.0,
        rvedvi_mL_m2=155.0,
    )
    assert res["tpvr_indicated"] is True
    assert res["recommended_valve_system"] == "MELODY_TPV_SYSTEM"
