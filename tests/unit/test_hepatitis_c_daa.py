"""
Unit tests for Chronic Hepatitis C DAA Regimen Engine
"""

from backend.ml.hepatitis_c_daa_regimen_engine import hcv_engine


def test_select_daa_treatment_naive():
    res = hcv_engine.select_daa_regimen(
        hcv_genotype="1A",
        compensated_cirrhosis=False,
    )
    assert res["recommended_regimen"] == "GLECAPREVIR_PIBRENTASVIR_8_WEEKS"
    assert res["duration_weeks"] == 8


def test_select_daa_decompensated():
    res = hcv_engine.select_daa_regimen(
        hcv_genotype="1B",
        decompensated_cirrhosis_child_pugh_b_c=True,
    )
    assert "SOFOSBUVIR_VELPATASVIR" in res["recommended_regimen"]
    assert res["duration_weeks"] == 12
    assert "CONTRAINDICATION" in res["clinical_recommendation"]
