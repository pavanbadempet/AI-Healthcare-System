"""
Unit tests for mEGRIS GBS Respiratory Engine
"""

from backend.ml.megris_gbs_respiratory_engine import megris_gbs_engine


def test_calculate_megris_score_high():
    res = megris_gbs_engine.calculate_megris_score(
        days_between_onset_and_admission=2,
        facial_or_bulbar_weakness_present=True,
        mrc_sum_score_0_to_60=25,
    )
    assert res["megris_total_score"] == 7
    assert res["one_week_mechanical_ventilation_risk_percent"] == 65.0
    assert res["stat_neuro_icu_and_intubation_prep_indicated"] is True
    assert "Neuro-ICU Transfer" in res["clinical_recommendation"]


def test_calculate_megris_score_low():
    res = megris_gbs_engine.calculate_megris_score(
        days_between_onset_and_admission=10,
        facial_or_bulbar_weakness_present=False,
        mrc_sum_score_0_to_60=55,
    )
    assert res["megris_total_score"] == 0
    assert res["one_week_mechanical_ventilation_risk_percent"] == 4.0
    assert res["stat_neuro_icu_and_intubation_prep_indicated"] is False
