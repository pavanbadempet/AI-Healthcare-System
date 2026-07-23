"""
Unit tests for Nursing Handoff Agent
"""

import pytest
from backend.agents.nursing_handoff_agent import NursingHandoffAgent, nursing_handoff_agent


def test_generate_sbar_handoff():
    res = nursing_handoff_agent.generate_sbar_handoff(
        patient_id=201,
        patient_name="Alice Walker",
        room_number="302-B",
        chief_complaint="Post-op Recovery",
        recent_vitals_summary="BP 118/76, HR 72, Temp 98.4F",
        active_iv_lines=["Normal Saline @ 75mL/h"],
        pending_labs=["CBC", "Electrolyte Panel"],
    )
    assert res["status"] == "HANDOFF_READY"
    assert "Alice Walker" in res["sbar"]["situation"]
    assert "CBC" in res["sbar"]["recommendation"]
