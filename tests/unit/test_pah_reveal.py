"""
Unit tests for PAH REVEAL Calculator
"""

from backend.ml.pah_reveal_risk_calculator import pah_reveal_calculator


def test_calculate_reveal_score_high():
    res = pah_reveal_calculator.calculate_reveal_score(
        nyha_functional_class=4,
        six_minute_walk_distance_meters=140.0,
        nt_probnp_pg_mL=1500.0,
        right_atrial_pressure_mmHg=16.0,
        pulmonary_vascular_resistance_wood_units=12.0,
    )
    assert res["reveal_2_0_score"] == 8
    assert res["pah_risk_category"] == "INTERMEDIATE_HIGH_RISK"
    assert res["triple_combination_therapy_indicated"] is True
    assert res["one_year_mortality_risk_percent"] == 12.0


def test_calculate_reveal_score_low():
    res = pah_reveal_calculator.calculate_reveal_score(
        nyha_functional_class=1,
        six_minute_walk_distance_meters=450.0,
        nt_probnp_pg_mL=120.0,
        right_atrial_pressure_mmHg=8.0,
        pulmonary_vascular_resistance_wood_units=4.0,
    )
    assert res["reveal_2_0_score"] == 0
    assert res["pah_risk_category"] == "LOW_RISK"
    assert res["triple_combination_therapy_indicated"] is False
