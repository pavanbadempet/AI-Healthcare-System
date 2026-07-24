"""
Unit tests for Autoimmune Pancreatitis Engine
"""

from backend.ml.autoimmune_pancreatitis_ig4_engine import autoimmune_pancreatitis_engine


def test_evaluate_hisort_criteria_type1():
    res = autoimmune_pancreatitis_engine.evaluate_hisort_criteria(
        serum_igg4_mg_dL=320.0,
        ct_mri_diffuse_sausage_shaped_enlargement=True,
        histology_lgpp_dense_igg4_plasma_cells=True,
        other_organ_involvement_retroperitoneal_fibrosis_or_cholangitis=True,
    )
    assert res["hisort_total_score"] >= 4
    assert res["aip_diagnosis"] == "TYPE_1_IGG4_RELATED_AUTOIMMUNE_PANCREATITIS"
    assert res["prednisone_steroid_therapy_indicated"] is True
    assert "Definite Type 1 IgG4-Related Autoimmune Pancreatitis" in res["clinical_recommendation"]


def test_evaluate_hisort_criteria_unlikely():
    res = autoimmune_pancreatitis_engine.evaluate_hisort_criteria(
        serum_igg4_mg_dL=85.0,
    )
    assert res["hisort_total_score"] == 0
    assert res["aip_diagnosis"] == "UNLIKELY_AUTOIMMUNE_PANCREATITIS"
    assert res["prednisone_steroid_therapy_indicated"] is False
