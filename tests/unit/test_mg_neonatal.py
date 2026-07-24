"""
Unit tests for MG Neonatal Transient Transfer Engine
"""

from backend.ml.mg_neonatal_transient_transfer_engine import neonatal_mg_engine


def test_evaluate_symptomatic_tnmg():
    res = neonatal_mg_engine.evaluate_transient_neonatal_mg(
        maternal_mg_diagnosed=True,
        maternal_achr_or_musk_antibody_positive=True,
        neonatal_poor_sucking_or_swallowing=True,
        neonatal_generalized_hypotonia=True,
    )
    assert res["maternal_mg_risk_present"] is True
    assert res["symptomatic_tnmg_diagnosed"] is True
    assert "ENTERAL_NEOSTIGMINE" in res["recommended_treatment"]
    assert "TRANSIENT NEONATAL MYASTHENIA GRAVIS" in res["clinical_recommendation"]


def test_evaluate_asymptomatic_neonatal_monitoring():
    res = neonatal_mg_engine.evaluate_transient_neonatal_mg(
        maternal_mg_diagnosed=True,
        maternal_achr_or_musk_antibody_positive=True,
        neonatal_poor_sucking_or_swallowing=False,
        neonatal_generalized_hypotonia=False,
    )
    assert res["maternal_mg_risk_present"] is True
    assert res["symptomatic_tnmg_diagnosed"] is False
