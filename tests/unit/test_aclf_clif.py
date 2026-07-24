"""
Unit tests for ACLF EASL-CLIF OF Engine
"""

from backend.ml.aclf_easl_clif_of_engine import aclf_clif_engine


def test_evaluate_aclf_grade_3():
    res = aclf_clif_engine.calculate_clif_c_ofs(
        total_bilirubin_mg_dL=15.0,  # 3 pts (liver OF)
        creatinine_mg_dL=2.5,  # 3 pts (kidney OF)
        hepatic_encephalopathy_grade=4,  # 3 pts (brain OF)
        inr_coagulation=1.2,
        mean_arterial_pressure_mmHg=80.0,
    )
    assert res["organ_failures_count"] == 3
    assert res["aclf_grade"] == "ACLF_GRADE_3"
    assert "CRITICAL ACLF GRADE 3" in res["clinical_recommendation"]


def test_evaluate_no_aclf():
    res = aclf_clif_engine.calculate_clif_c_ofs(
        total_bilirubin_mg_dL=2.0,
        creatinine_mg_dL=0.9,
        hepatic_encephalopathy_grade=0,
        inr_coagulation=1.1,
        mean_arterial_pressure_mmHg=85.0,
    )
    assert res["organ_failures_count"] == 0
    assert res["aclf_grade"] == "NO_ACLF"
