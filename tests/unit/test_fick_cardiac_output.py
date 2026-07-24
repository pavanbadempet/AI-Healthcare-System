"""
Unit tests for Invasive Fick Cardiac Output Engine
"""

from backend.ml.fick_cardiac_output_engine import fick_engine


def test_calculate_fick_cardiac_output_cardiogenic():
    res = fick_engine.calculate_fick_cardiac_output(
        oxygen_consumption_vo2_mL_min=250.0,
        hemoglobin_g_dL=12.0,
        arterial_sat_sao2_percent=95.0,
        mixed_venous_sat_svo2_percent=55.0,
        mean_arterial_pressure_mmHg=80.0,
        central_venous_pressure_mmHg=15.0,
    )
    assert res["cardiac_output_L_min"] < 4.0
    assert res["systemic_vascular_resistance_dynes"] > 1200
    assert res["hemodynamic_shock_classification"] == "CARDIOGENIC_SHOCK"


def test_calculate_fick_cardiac_output_normal():
    res = fick_engine.calculate_fick_cardiac_output(
        oxygen_consumption_vo2_mL_min=250.0,
        hemoglobin_g_dL=14.0,
        arterial_sat_sao2_percent=98.0,
        mixed_venous_sat_svo2_percent=75.0,
        mean_arterial_pressure_mmHg=90.0,
        central_venous_pressure_mmHg=6.0,
    )
    assert res["cardiac_output_L_min"] >= 5.0
    assert res["hemodynamic_shock_classification"] == "NORMAL_HEMODYNAMICS"
