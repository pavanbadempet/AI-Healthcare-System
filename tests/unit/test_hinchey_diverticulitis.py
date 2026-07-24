"""
Unit tests for Hinchey Diverticulitis Engine
"""

from backend.ml.hinchey_diverticulitis_engine import hinchey_engine


def test_stage_hinchey_diverticulitis_stage_iv():
    res = hinchey_engine.stage_hinchey_diverticulitis(
        fecal_peritonitis_gross_contamination=True,
    )
    assert res["hinchey_stage"] == "HINCHEY_STAGE_IV_FECAL_PERITONITIS"
    assert res["emergency_surgery_indicated"] is True
    assert "Hartmann's Resection" in res["clinical_recommendation"]


def test_stage_hinchey_diverticulitis_uncomplicated():
    res = hinchey_engine.stage_hinchey_diverticulitis()
    assert res["hinchey_stage"] == "UNCOMPLICATED_DIVERTICULITIS"
    assert res["emergency_surgery_indicated"] is False
