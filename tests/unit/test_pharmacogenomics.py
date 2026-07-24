"""
Unit tests for Pharmacogenomics Engine
"""

import pytest
from backend.ml.pharmacogenomics_engine import PharmacogenomicsEngine, pgx_engine


def test_evaluate_pgx_dosing_alert():
    res = pgx_engine.evaluate_pgx_dosing(
        medication_name="Clopidogrel",
        gene="CYP2C19",
        diplotype="*2/*2",
    )
    assert res["is_pgx_alert"] is True
    assert res["metabolizer_phenotype"] == "POOR"
    assert res["pgx_recommendation_action"] == "CONTRAINDICATED"


def test_evaluate_pgx_dosing_standard():
    res = pgx_engine.evaluate_pgx_dosing(
        medication_name="Clopidogrel",
        gene="CYP2C19",
        diplotype="*1/*1",
    )
    assert res["is_pgx_alert"] is False
    assert res["pgx_recommendation_action"] == "STANDARD_DOSING"
