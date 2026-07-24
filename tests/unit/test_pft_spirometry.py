"""
Unit tests for PFT Spirometry Interpreter
"""

from backend.ml.pft_spirometry_interpreter import pft_interpreter


def test_interpret_spirometry_obstructive():
    res = pft_interpreter.interpret_spirometry(
        fev1_liters=1.8,
        fvc_liters=3.2,
        fev1_percent_predicted=45.0,
    )
    assert res["spirometry_pattern"] == "OBSTRUCTIVE_DEFECT"
    assert res["defect_severity"] == "SEVERE"
    assert res["fev1_fvc_ratio_percent"] < 70.0


def test_interpret_spirometry_normal():
    res = pft_interpreter.interpret_spirometry(
        fev1_liters=3.5,
        fvc_liters=4.2,
        fev1_percent_predicted=95.0,
    )
    assert res["spirometry_pattern"] == "NORMAL_SPIROMETRY"
    assert res["defect_severity"] == "NORMAL"
