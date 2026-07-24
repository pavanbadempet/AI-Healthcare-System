"""
Unit tests for Chronic HBV Functional Cure Engine
"""

from backend.ml.hepatitis_b_functional_cure_engine import hbv_cure_engine


def test_evaluate_functional_cure_achieved():
    res = hbv_cure_engine.evaluate_functional_cure(
        hbsag_quantitative_iu_mL=0.01,
        anti_hbs_mIU_mL=125.0,
        hbv_dna_iu_mL=0.0,
        cirrhosis_present=False,
        months_of_sustained_hbsag_loss=12.0,
    )
    assert res["functional_cure_achieved"] is True
    assert res["safe_to_discontinue_antiviral"] is True
    assert "PHASE 5 FUNCTIONAL CURE" in res["clinical_recommendation"]


def test_evaluate_functional_cure_cirrhotic_continue():
    res = hbv_cure_engine.evaluate_functional_cure(
        hbsag_quantitative_iu_mL=0.02,
        anti_hbs_mIU_mL=45.0,
        hbv_dna_iu_mL=0.0,
        cirrhosis_present=True,
    )
    assert res["functional_cure_achieved"] is True
    assert res["safe_to_discontinue_antiviral"] is False
