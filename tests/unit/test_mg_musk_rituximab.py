"""
Unit tests for MG MuSK Rituximab Protocol Engine
"""

from backend.ml.mg_musk_rituximab_protocol_engine import musk_rituximab_engine


def test_evaluate_musk_rituximab_fixed_dose():
    res = musk_rituximab_engine.evaluate_musk_rituximab_protocol(
        musk_antibody_positive=True,
        months_since_last_rituximab_infusion=0.0,
        dosing_regimen_type="FIXED_DOSE_1000MG",
    )
    assert res["rituximab_indicated"] is True
    assert "1000 mg IV on Day 1 and Day 15" in res["recommended_regimen"]
    assert "RITUXIMAB INDICATED FOR MuSK+" in res["clinical_recommendation"]


def test_evaluate_musk_rituximab_bcell_depleted_hold():
    res = musk_rituximab_engine.evaluate_musk_rituximab_protocol(
        musk_antibody_positive=True,
        cd19_cd20_b_cell_percent=0.01,  # Still depleted
        months_since_last_rituximab_infusion=6.0,
    )
    assert res["rituximab_indicated"] is False
