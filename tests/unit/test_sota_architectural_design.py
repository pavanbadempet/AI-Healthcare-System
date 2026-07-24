"""
Unit tests for SOTA Architectural Design System Engine (backend/sota_architectural_design.py).
"""

from backend.sota_architectural_design import (
    ClinicalQueryView,
    SOTAArchitecturalDesignEngine,
)


def test_cqrs_read_view_and_event_publishing():
    engine = SOTAArchitecturalDesignEngine()

    view = ClinicalQueryView(
        patient_id="PAT_9001",
        active_prescriptions_count=3,
        latest_vitals_summary="BP 120/80, HR 72",
        risk_level="MEDIUM",
    )

    engine.update_patient_read_view(view)
    fetched_view = engine.get_patient_read_view("PAT_9001")

    assert fetched_view.patient_id == "PAT_9001"
    assert fetched_view.active_prescriptions_count == 3
    assert fetched_view.risk_level == "MEDIUM"

    engine.publish_domain_event("PATIENT_ADMITTED", {"patient_id": "PAT_9001"})
    assert len(engine.published_events) == 1
    assert engine.published_events[0]["event_type"] == "PATIENT_ADMITTED"
