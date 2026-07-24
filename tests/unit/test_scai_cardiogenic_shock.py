"""
Unit tests for SCAI Cardiogenic Shock Engine
"""

from backend.ml.scai_cardiogenic_shock_engine import scai_shock_engine


def test_stage_cardiogenic_shock_stage_d():
    res = scai_shock_engine.stage_cardiogenic_shock(
        systolic_bp_mmHg=82,
        lactate_mmol_L=5.2,
        cardiac_index_L_min_m2=1.6,
        on_inotropes_or_vasopressors=True,
        on_mechanical_circulatory_support=True,
    )
    assert res["scai_shock_stage"] == "STAGE_D_DETERIORATING"
    assert res["shock_team_activation_indicated"] is True
    assert "Shock Team Activation" in res["clinical_recommendation"]


def test_stage_cardiogenic_shock_stage_a():
    res = scai_shock_engine.stage_cardiogenic_shock(
        systolic_bp_mmHg=125,
        lactate_mmol_L=1.0,
        cardiac_index_L_min_m2=2.8,
    )
    assert res["scai_shock_stage"] == "STAGE_A_AT_RISK"
    assert res["shock_team_activation_indicated"] is False
