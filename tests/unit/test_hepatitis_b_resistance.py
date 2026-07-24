"""
Unit tests for Chronic Hepatitis B Antiviral Resistance Engine
"""

from backend.ml.hepatitis_b_antiviral_resistance_engine import hbv_resistance_engine


def test_evaluate_entecavir_resistance():
    res = hbv_resistance_engine.evaluate_hbv_resistance(
        detected_mutations=["rtM204V", "rtL180M", "rtT184G"],
        current_antiviral="ENTECAVIR",
    )
    assert res["resistance_detected"] is True
    assert res["entecavir_resistant"] is True
    assert "SWITCH_TO_TENOFOVIR_ALAFENAMIDE" in res["recommended_rescue_regimen"]


def test_evaluate_no_resistance():
    res = hbv_resistance_engine.evaluate_hbv_resistance(
        detected_mutations=[],
    )
    assert res["resistance_detected"] is False
    assert res["recommended_rescue_regimen"] == "CONTINUE_CURRENT_ANTIVIRAL_MONITOR_Q3M"
