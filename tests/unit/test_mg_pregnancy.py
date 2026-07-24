"""
Unit tests for MG Pregnancy & Teratogenicity Engine
"""

from backend.ml.mg_pregnancy_teratogenicity_engine import mg_pregnancy_engine


def test_evaluate_teratogenic_mycophenolate():
    res = mg_pregnancy_engine.evaluate_pregnancy_drug_safety(
        current_medications=["Pyridostigmine", "Mycophenolate Mofetil"],
        patient_currently_pregnant=True,
    )
    assert res["has_teratogenic_medication"] is True
    assert "MYCOPHENOLATE MOFETIL" in res["strictly_contraindicated_drugs"]
    assert res["action_required"] == "IMMEDIATELY_DISCONTINUE_TERATOGENIC_DRUG_AND_SWITCH_TO_PREDNISONE_OR_AZATHIOPRINE"
    assert "CRITICAL CONTRAINDICATION IN PREGNANCY" in res["clinical_recommendation"]


def test_evaluate_safe_pregnancy_regimen():
    res = mg_pregnancy_engine.evaluate_pregnancy_drug_safety(
        current_medications=["Pyridostigmine", "Prednisone", "IVIG"],
        patient_currently_pregnant=True,
    )
    assert res["has_teratogenic_medication"] is False
    assert res["action_required"] == "CONTINUE_SAFE_MG_THERAPY"
