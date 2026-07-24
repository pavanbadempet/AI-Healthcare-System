"""
Unit tests for Light's Criteria Classifier
"""

from backend.ml.lights_criteria_classifier import lights_classifier


def test_classify_pleural_effusion_exudate():
    res = lights_classifier.classify_pleural_effusion(
        pleural_fluid_protein_g_dL=4.2,
        serum_protein_g_dL=6.5,
        pleural_fluid_ldh_IU_L=280.0,
        serum_ldh_IU_L=310.0,
    )
    assert res["effusion_type"] == "EXUDATE"
    assert res["pleural_serum_protein_ratio"] > 0.5
    assert "cytology" in res["further_workup"]


def test_classify_pleural_effusion_transudate():
    res = lights_classifier.classify_pleural_effusion(
        pleural_fluid_protein_g_dL=1.8,
        serum_protein_g_dL=6.8,
        pleural_fluid_ldh_IU_L=80.0,
        serum_ldh_IU_L=220.0,
    )
    assert res["effusion_type"] == "TRANSUDATE"
    assert res["pleural_serum_protein_ratio"] <= 0.5
