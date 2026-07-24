"""
Unit tests for FFR Coronary Stenosis Engine
"""

from backend.ml.ffr_coronary_stenosis_engine import ffr_coronary_engine


def test_evaluate_coronary_ischemia_positive():
    res = ffr_coronary_engine.evaluate_coronary_ischemia(
        pd_pa_hyperemic_ffr=0.74,
        instantaneous_wave_free_ratio_ifr=0.85,
        angiographic_stenosis_percent=65.0,
    )
    assert res["hemodynamically_significant_ischemia"] is True
    assert res["pci_revascularization_indicated"] is True
    assert "Percutaneous Coronary Intervention" in res["clinical_recommendation"]


def test_evaluate_coronary_ischemia_negative():
    res = ffr_coronary_engine.evaluate_coronary_ischemia(
        pd_pa_hyperemic_ffr=0.86,
        instantaneous_wave_free_ratio_ifr=0.92,
        angiographic_stenosis_percent=55.0,
    )
    assert res["hemodynamically_significant_ischemia"] is False
    assert res["pci_revascularization_indicated"] is False
