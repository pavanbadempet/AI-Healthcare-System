"""
Unit tests for MG Biologic Refractory Engine
"""

from backend.ml.mg_biologic_refractory_engine import mg_biologic_engine


def test_evaluate_musk_mg_rituximab():
    res = mg_biologic_engine.evaluate_biologic_candidate(
        musk_antibody_positive=True,
        achr_antibody_positive=False,
    )
    assert res["biologic_indicated"] is True
    assert "RITUXIMAB" in res["recommended_biologic"]
    assert "Anti-MuSK MG responds exceptionally to B-cell depletion" in res["clinical_recommendation"]


def test_evaluate_achr_mg_standard_care():
    res = mg_biologic_engine.evaluate_biologic_candidate(
        musk_antibody_positive=False,
        achr_antibody_positive=True,
        refractory_to_steroids_or_isrs=False,
    )
    assert res["biologic_indicated"] is False
