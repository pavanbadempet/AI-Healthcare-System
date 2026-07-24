"""
Unit tests for Tumor Board Agent
"""

import pytest
from backend.agents.tumor_board_agent import TumorBoardAgent, tumor_board_agent


def test_generate_tumor_board_summary():
    res = tumor_board_agent.generate_tumor_board_summary(
        patient_id=501,
        patient_name="Sarah Connor",
        cancer_type="Non-Small Cell Lung Cancer (NSCLC)",
        tnm_stage="T2N1M0 (Stage IIB)",
        pathology_summary="Adenocarcinoma, moderately differentiated.",
        genomic_biomarkers={"EGFR": "L858R Mutated", "ALK": "Negative"},
        prior_therapies=["Right Upper Lobectomy"],
    )
    assert res["board_review_status"] == "READY_FOR_MDT_PRESENTATION"
    assert res["has_actionable_genomic_target"] is True
    assert "Sarah Connor" in res["summary_card"]
