"""
Unit tests for PAH Sotatercept Eligibility Engine
"""

from backend.ml.pah_sotatercept_eligibility_engine import sotatercept_engine


def test_evaluate_sotatercept_eligible():
    res = sotatercept_engine.evaluate_sotatercept_eligibility(
        who_group=1,
        pulmonary_vascular_resistance_wood_units=6.5,
        who_functional_class=3,
        on_background_dual_or_triple_pah_therapy=True,
        hemoglobin_g_dL=13.5,
        platelet_count_per_uL=180000.0,
        patient_weight_kg=70.0,
    )
    assert res["eligible_for_sotatercept"] is True
    assert res["initial_dose_mg"] == 21.0
    assert res["target_maintenance_dose_mg"] == 49.0
    assert "ELIGIBLE FOR SOTATERCEPT" in res["clinical_recommendation"]


def test_evaluate_sotatercept_high_hb_ineligible():
    res = sotatercept_engine.evaluate_sotatercept_eligibility(
        who_group=1,
        pulmonary_vascular_resistance_wood_units=6.5,
        who_functional_class=3,
        hemoglobin_g_dL=17.2,
    )
    assert res["eligible_for_sotatercept"] is False
