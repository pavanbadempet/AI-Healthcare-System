"""
Unit tests for Myasthenic Crisis PLEX vs IVIG Selection Engine
"""

from backend.ml.myasthenic_crisis_plex_ivig_selection_engine import plex_ivig_engine


def test_select_plex_intubated_crisis():
    res = plex_ivig_engine.select_crisis_modality(
        respiratory_failure_intubated=True,
        hyperviscosity_risk_or_thrombosis=False,
    )
    assert res["selected_modality"] == "PLASMA_EXCHANGE_PLEX"
    assert "5 to 6 plasma exchanges" in res["recommended_dosage_regimen"]


def test_select_ivig_difficult_access():
    res = plex_ivig_engine.select_crisis_modality(
        respiratory_failure_intubated=True,
        difficult_central_venous_access=True,
    )
    assert res["selected_modality"] == "HIGH_DOSE_IVIG"
    assert "2.0 g/kg" in res["recommended_dosage_regimen"]
