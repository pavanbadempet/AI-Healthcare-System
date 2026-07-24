"""
Unit tests for Renal Artery Stenosis Engine
"""

from backend.ml.renal_artery_stenosis_engine import ras_engine


def test_evaluate_ras_risk_high():
    res = ras_engine.evaluate_ras_risk(
        refractory_hypertension_3_or_more_meds=True,
        creatinine_rise_over_30pct_after_acei_arb=True,
        abdominal_bruit_present=True,
        duplex_psv_cm_s=220.0,
    )
    assert res["ras_risk_score"] == 8
    assert res["high_probability_ras"] is True
    assert "MR Angiography" in res["diagnostic_imaging_recommendation"]


def test_evaluate_ras_risk_low():
    res = ras_engine.evaluate_ras_risk(
        refractory_hypertension_3_or_more_meds=False,
        creatinine_rise_over_30pct_after_acei_arb=False,
        duplex_psv_cm_s=110.0,
    )
    assert res["ras_risk_score"] == 0
    assert res["high_probability_ras"] is False
