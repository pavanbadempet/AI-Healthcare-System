"""
Unit tests for Autoimmune Hepatitis Remission Engine
"""

from backend.ml.autoimmune_hepatitis_remission_engine import aih_remission_engine


def test_evaluate_withdrawal_safe():
    res = aih_remission_engine.evaluate_remission_and_withdrawal(
        months_of_normal_alt_ast=30.0,
        months_of_normal_serum_igg=30.0,
        ishak_hepatitis_activity_index=2,
        cirrhosis_present=False,
    )
    assert res["biochemical_remission"] is True
    assert res["histologic_remission"] is True
    assert res["safe_to_attempt_withdrawal"] is True
    assert "COMPLETE BIOCHEMICAL & HISTOLOGIC REMISSION" in res["clinical_recommendation"]


def test_evaluate_withdrawal_cirrhotic_continue():
    res = aih_remission_engine.evaluate_remission_and_withdrawal(
        months_of_normal_alt_ast=36.0,
        months_of_normal_serum_igg=36.0,
        ishak_hepatitis_activity_index=1,
        cirrhosis_present=True,
    )
    assert res["safe_to_attempt_withdrawal"] is False
    assert "BIOCHEMICAL REMISSION IN CIRRHOSIS" in res["clinical_recommendation"]
