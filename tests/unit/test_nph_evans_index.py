"""
Unit tests for NPH Evan's Index & Tap Test Engine
"""

from backend.ml.nph_evans_index_tap_test_engine import nph_engine


def test_evaluate_nph_high_probability_shunt():
    res = nph_engine.evaluate_nph_shunt_candidacy(
        evans_index=0.36,
        gait_ataxia_present=True,
        cognitive_decline_present=True,
        urinary_incontinence_present=True,
        csf_tap_test_gait_speed_improvement_pct=28.0,
    )
    assert res["nph_confirmed"] is True
    assert res["positive_tap_test"] is True
    assert res["shunt_candidacy"] == "HIGH_PROBABILITY_VP_SHUNT_RESPONDER"
    assert "Programmable Ventriculoperitoneal (VP) Shunt" in res["clinical_recommendation"]


def test_evaluate_nph_ineligible():
    res = nph_engine.evaluate_nph_shunt_candidacy(
        evans_index=0.25,  # evans < 0.30
        gait_ataxia_present=False,
        cognitive_decline_present=True,
        urinary_incontinence_present=False,
        csf_tap_test_gait_speed_improvement_pct=5.0,
    )
    assert res["nph_confirmed"] is False
    assert res["shunt_candidacy"] == "INELIGIBLE"
