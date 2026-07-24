"""
Unit tests for Acute UGIB Glasgow-Blatchford Outpatient Engine
"""

from backend.ml.ugib_glasgow_blatchford_outpatient_engine import gbs_outpatient_engine


def test_evaluate_gbs_safe_outpatient():
    res = gbs_outpatient_engine.evaluate_outpatient_safety(
        blood_urea_nitrogen_mg_dL=12.0,
        hemoglobin_g_dL=14.5,
        sex_male=True,
        systolic_bp_mmHg=125.0,
        pulse_bpm=72.0,
    )
    assert res["gbs_score"] == 0
    assert res["safe_for_outpatient_discharge"] is True
    assert "SAFE FOR OUTPATIENT DISCHARGE" in res["clinical_recommendation"]


def test_evaluate_gbs_inpatient_needed():
    res = gbs_outpatient_engine.evaluate_outpatient_safety(
        blood_urea_nitrogen_mg_dL=25.0,  # 3 pts
        hemoglobin_g_dL=11.2,  # 3 pts
        sex_male=True,
    )
    assert res["gbs_score"] >= 2
    assert res["safe_for_outpatient_discharge"] is False
