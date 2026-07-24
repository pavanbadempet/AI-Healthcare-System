"""
Unit tests for Chronic HDV Response Engine
"""

from backend.ml.hdv_pegifn_bulevirtide_response_engine import hdv_response_engine


def test_evaluate_hdv_combined_response():
    res = hdv_response_engine.evaluate_hdv_response(
        baseline_hdv_rna_iu_mL=500000.0,
        week_24_hdv_rna_iu_mL=200.0,  # ~3.4 log drop
        alt_u_L=28.0,
    )
    assert res["virological_response_met"] is True
    assert res["combined_response_achieved"] is True
    assert res["hdv_rna_log10_decline"] >= 3.0


def test_evaluate_hdv_suboptimal_response():
    res = hdv_response_engine.evaluate_hdv_response(
        baseline_hdv_rna_iu_mL=500000.0,
        week_24_hdv_rna_iu_mL=100000.0,  # ~0.7 log drop
        alt_u_L=85.0,
    )
    assert res["virological_response_met"] is False
    assert res["combined_response_achieved"] is False
