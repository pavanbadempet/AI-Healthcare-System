"""
Unit tests for Radiology Pre-Reader Agent
"""

import pytest
from backend.agents.radiology_prereader_agent import RadiologyPreReaderAgent, radiology_prereader_agent


def test_generate_pre_read_impression_stat():
    res = radiology_prereader_agent.generate_pre_read_impression(
        modality="CXRAY",
        clinical_indication="Shortness of breath after trauma",
        detected_findings=["Right-sided tension pneumothorax", "Rib fracture"],
    )
    assert res["urgency_level"] == "CRITICAL_STAT"
    assert res["requires_stat_radiologist_alert"] is True
    assert "pneumothorax" in res["impression_text"].lower()


def test_generate_pre_read_impression_routine():
    res = radiology_prereader_agent.generate_pre_read_impression(
        modality="CXRAY",
        clinical_indication="Routine pre-op clearance",
        detected_findings=["Lungs clear without consolidation"],
    )
    assert res["urgency_level"] == "ROUTINE"
    assert res["requires_stat_radiologist_alert"] is False
