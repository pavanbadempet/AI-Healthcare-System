"""
Unit tests for Chronic HBV TAF Renal & Bone Safety Engine
"""

from backend.ml.hepatitis_b_taf_renal_bone_safety_engine import hbv_taf_engine


def test_evaluate_taf_switch_for_osteoporosis():
    res = hbv_taf_engine.evaluate_taf_switch_indication(
        current_antiviral="TDF",
        egfr_mL_min_1_73m2=75.0,
        bone_mineral_density_t_score=-2.8,
    )
    assert res["switch_from_tdf_indicated"] is True
    assert res["recommended_alternative_antiviral"] == "TAF_25MG_DAILY"
    assert "SWITCH FROM TDF INDICATED" in res["clinical_recommendation"]


def test_evaluate_taf_continue_tdf():
    res = hbv_taf_engine.evaluate_taf_switch_indication(
        current_antiviral="TDF",
        egfr_mL_min_1_73m2=92.0,
        bone_mineral_density_t_score=-0.5,
        age_years=40,
    )
    assert res["switch_from_tdf_indicated"] is False
