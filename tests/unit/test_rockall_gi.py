"""
Unit tests for Rockall GI Bleed Engine
"""

from backend.ml.rockall_gi_bleed_engine import rockall_gi_engine


def test_calculate_rockall_score_high():
    res = rockall_gi_engine.calculate_rockall_score(
        age_years=82,
        shock_state="HYPOTENSION",
        comorbidities="RENAL_LIVER_MALIGNANCY",
        endoscopic_diagnosis="GI_MALIGNANCY",
        stigmata_of_hemorrhage="ACTIVE_BLEEDING_SPURTING",
    )
    assert res["rockall_total_score"] == 11
    assert res["risk_tier"] == "HIGH_RISK"
    assert res["icu_admission_and_iv_ppi_indicated"] is True
    assert "IV Pantoprazole infusion" in res["clinical_recommendation"]


def test_calculate_rockall_score_low():
    res = rockall_gi_engine.calculate_rockall_score(
        age_years=45,
        shock_state="NO_SHOCK",
        comorbidities="NONE",
        endoscopic_diagnosis="NO_LESION_MALORY_WEISS",
        stigmata_of_hemorrhage="NONE",
    )
    assert res["rockall_total_score"] == 0
    assert res["risk_tier"] == "LOW_RISK"
    assert res["icu_admission_and_iv_ppi_indicated"] is False
