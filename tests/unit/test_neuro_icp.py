"""
Unit tests for Neuro-ICU ICP Monitor
"""

from backend.ml.neuro_icp_monitor import neuro_icp_monitor


def test_evaluate_cerebral_perfusion_critical():
    res = neuro_icp_monitor.evaluate_cerebral_perfusion(
        mean_arterial_pressure_mmHg=75.0,
        intracranial_pressure_mmHg=26.0,
    )
    assert res["herniation_risk"] is True
    assert res["cerebral_perfusion_pressure"] == 49.0
    assert "Hypertonic Saline" in res["recommended_intervention"]


def test_evaluate_cerebral_perfusion_normal():
    res = neuro_icp_monitor.evaluate_cerebral_perfusion(
        mean_arterial_pressure_mmHg=85.0,
        intracranial_pressure_mmHg=14.0,
    )
    assert res["herniation_risk"] is False
    assert res["cerebral_perfusion_pressure"] == 71.0
