"""
Unit tests for Hepatic Encephalopathy Staging Engine
"""

from backend.ml.hepatic_encephalopathy_staging import hepatic_encephalopathy_engine


def test_stage_hepatic_encephalopathy_grade4():
    res = hepatic_encephalopathy_engine.stage_hepatic_encephalopathy(
        asterixis_present=True,
        disoriented_to_time_place=True,
        somnolent_or_stuporous=True,
        comatose=True,
        serum_ammonia_umol_L=140.0,
    )
    assert res["west_haven_grade"] == "GRADE_4_COMA"
    assert res["requires_icu_intubation"] is True
    assert "ICU admission" in res["pharmacotherapy_recommendation"]


def test_stage_hepatic_encephalopathy_grade0():
    res = hepatic_encephalopathy_engine.stage_hepatic_encephalopathy(
        asterixis_present=False,
        disoriented_to_time_place=False,
        somnolent_or_stuporous=False,
        comatose=False,
        serum_ammonia_umol_L=35.0,
    )
    assert res["west_haven_grade"] == "GRADE_0_SUBCLINICAL"
    assert res["requires_icu_intubation"] is False
