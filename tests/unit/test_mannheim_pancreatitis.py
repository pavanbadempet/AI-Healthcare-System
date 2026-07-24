"""
Unit tests for M-ANNHEIM Chronic Pancreatitis Engine
"""

from backend.ml.mannheim_chronic_pancreatitis_engine import mannheim_pancreatitis_engine


def test_stage_mannheim_chronic_pancreatitis_stage3():
    res = mannheim_pancreatitis_engine.stage_mannheim_chronic_pancreatitis(
        pancreatic_duct_stone_or_stricture=True,
        persistent_intractable_pain=True,
    )
    assert res["mannheim_stage"] == "STAGE_M3_COMPLICATED_OBSTRUCTIVE"
    assert res["endoscopic_or_surgical_decompression_indicated"] is True
    assert "Frey / Puestow Procedure" in res["clinical_recommendation"]


def test_stage_mannheim_chronic_pancreatitis_subclinical():
    res = mannheim_pancreatitis_engine.stage_mannheim_chronic_pancreatitis()
    assert res["mannheim_stage"] == "STAGE_M0_SUBCLINICAL"
    assert res["endoscopic_or_surgical_decompression_indicated"] is False
