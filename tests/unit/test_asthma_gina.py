"""
Unit tests for Asthma GINA Treatment Engine
"""

from backend.ml.asthma_gina_treatment_engine import asthma_gina_engine


def test_evaluate_gina_treatment_step4():
    res = asthma_gina_engine.evaluate_gina_treatment(
        daytime_symptoms_per_week=7,
        night_awakenings_per_month=6,
        fev1_percent_predicted=52.0,
        exacerbations_requiring_oral_steroids_past_year=2,
    )
    assert res["gina_step_recommendation"] == "STEP_4_5"
    assert res["asthma_uncontrolled"] is True
    assert res["biologic_eval_indicated"] is True
    assert "Biologic add-on" in res["recommended_pharmacotherapy_track_1"]


def test_evaluate_gina_treatment_step1():
    res = asthma_gina_engine.evaluate_gina_treatment(
        daytime_symptoms_per_week=1,
        night_awakenings_per_month=0,
        fev1_percent_predicted=92.0,
        exacerbations_requiring_oral_steroids_past_year=0,
    )
    assert res["gina_step_recommendation"] == "STEP_1_2"
    assert res["asthma_uncontrolled"] is False
    assert res["biologic_eval_indicated"] is False
