"""
Unit tests for PAH RHC Hemodynamic Engine
"""

from backend.ml.pah_rhc_hemodynamic_engine import rhc_engine


def test_evaluate_pre_capillary_pah():
    res = rhc_engine.evaluate_rhc_hemodynamics(
        mean_pap_mmHg=38.0,
        pcwp_mmHg=11.0,
        pvr_wood_units=5.2,
    )
    assert res["ph_classification"] == "GROUP_1_PRE_CAPILLARY_PAH"
    assert "PRE-CAPILLARY PAH DIAGNOSED" in res["clinical_recommendation"]


def test_evaluate_normal_hemodynamics():
    res = rhc_engine.evaluate_rhc_hemodynamics(
        mean_pap_mmHg=16.0,
        pcwp_mmHg=9.0,
        pvr_wood_units=1.2,
    )
    assert res["ph_classification"] == "NO_PULMONARY_HYPERTENSION"
