"""
Unit tests for QTc Prolongation Calculator
"""

from backend.ml.qtc_prolongation_calculator import qtc_calculator


def test_calculate_qtc_high_risk_tdp():
    res = qtc_calculator.calculate_qtc(
        qt_interval_ms=480.0,
        heart_rate_bpm=75,
        female_sex=True,
        on_qt_prolonging_meds=True,
    )
    assert res["qtc_bazett_ms"] >= 500.0
    assert res["qtc_prolonged"] is True
    assert res["torsades_de_pointes_high_risk"] is True
    assert "Discontinue QT-prolonging" in res["clinical_recommendation"]


def test_calculate_qtc_normal():
    res = qtc_calculator.calculate_qtc(
        qt_interval_ms=380.0,
        heart_rate_bpm=65,
        female_sex=False,
    )
    assert res["qtc_prolonged"] is False
    assert res["torsades_de_pointes_high_risk"] is False
