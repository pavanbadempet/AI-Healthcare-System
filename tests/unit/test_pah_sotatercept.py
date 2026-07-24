"""
Unit tests for PAH Sotatercept Activin Engine
"""

from backend.ml.pah_sotatercept_activin_engine import sotatercept_engine


def test_evaluate_sotatercept_eligible():
    res = sotatercept_engine.evaluate_sotatercept_eligibility(
        who_group_1_pah_confirmed=True,
        on_background_era_pde5i_prostacyclin=True,
        hemoglobin_g_dL=13.5,
        platelet_count_per_uL=150000.0,
    )
    assert res["sotatercept_indicated"] is True
    assert "SOTATERCEPT_0.3_MG_KG" in res["recommended_starting_dose"]
    assert "ELIGIBLE FOR SOTATERCEPT" in res["clinical_recommendation"]


def test_evaluate_sotatercept_polycythemia_hold():
    res = sotatercept_engine.evaluate_sotatercept_eligibility(
        who_group_1_pah_confirmed=True,
        on_background_era_pde5i_prostacyclin=True,
        hemoglobin_g_dL=16.8,  # Polycythemia
    )
    assert res["safety_clearance"] is False
    assert res["sotatercept_indicated"] is False
