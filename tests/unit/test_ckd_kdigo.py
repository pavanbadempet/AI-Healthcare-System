"""
Unit tests for CKD KDIGO Risk Matrix Engine
"""

from backend.ml.ckd_kdigo_risk_matrix import ckd_kdigo_engine


def test_evaluate_ckd_kdigo_stage_very_high():
    res = ckd_kdigo_engine.evaluate_ckd_kdigo_stage(
        egfr_mL_min_1_73m2=22.0,
        urine_albumin_creatinine_ratio_mg_g=450.0,
    )
    assert res["egfr_stage"] == "G4_SEVERELY_DECREASED"
    assert res["albuminuria_category"] == "A3_SEVERELY_INCREASED"
    assert res["ckd_kdigo_risk_tier"] == "VERY_HIGH_RISK"
    assert res["nephrology_referral_recommended"] is True


def test_evaluate_ckd_kdigo_stage_low():
    res = ckd_kdigo_engine.evaluate_ckd_kdigo_stage(
        egfr_mL_min_1_73m2=95.0,
        urine_albumin_creatinine_ratio_mg_g=12.0,
    )
    assert res["egfr_stage"] == "G1_NORMAL_OR_HIGH"
    assert res["albuminuria_category"] == "A1_NORMAL_TO_MILDLY_INCREASED"
    assert res["ckd_kdigo_risk_tier"] == "LOW_RISK"
    assert res["nephrology_referral_recommended"] is False
