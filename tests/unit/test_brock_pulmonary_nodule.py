"""
Unit tests for Brock Pulmonary Nodule Model
"""

from backend.ml.brock_pulmonary_nodule_model import brock_nodule_model


def test_calculate_nodule_malignancy_probability_high():
    res = brock_nodule_model.calculate_nodule_malignancy_probability(
        nodule_diameter_mm=22.0,
        female_sex=True,
        spiculation_present=True,
        upper_lobe_location=True,
        part_solid_or_nonsolid=True,
        family_history_lung_cancer=True,
        emphysema_present=True,
    )
    assert res["two_year_cancer_probability_percent"] >= 65.0
    assert res["risk_tier"] == "HIGH_RISK"
    assert res["tissue_biopsy_or_resection_indicated"] is True
    assert "Surgical resection" in res["fleischner_guideline_recommendation"]


def test_calculate_nodule_malignancy_probability_low():
    res = brock_nodule_model.calculate_nodule_malignancy_probability(
        nodule_diameter_mm=4.0,
        female_sex=False,
        spiculation_present=False,
        upper_lobe_location=False,
    )
    assert res["two_year_cancer_probability_percent"] < 10.0
    assert res["risk_tier"] == "LOW_RISK"
    assert res["tissue_biopsy_or_resection_indicated"] is False
