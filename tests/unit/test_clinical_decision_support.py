import time
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.audit_log import clear_audit_logs, get_logged_audit_events, log_clinical_access_event
from backend.cds_hooks import evaluate_cardio_risk_service, get_cds_services_registry
from backend.database import Base
from backend.models.auth import User
from backend.models.clinical import VitalObservation
from backend.subscriptions import (
    clear_subscriptions,
    dispatch_observation_notifications,
    get_active_subscriptions,
    register_fhir_subscription,
)

# ── DB fixture ────────────────────────────────────────────────────────────────

@pytest.fixture
def db():
    """Isolated in-memory SQLite database setup for CDS and auditing tests."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)

# ── CDS Hooks Tests ───────────────────────────────────────────────────────────

def test_cds_hooks_discovery_and_evaluation(db):
    # 1. Test Registry Discovery
    registry = get_cds_services_registry()
    assert "services" in registry
    assert len(registry["services"]) == 1
    assert registry["services"][0]["id"] == "cardio-risk-service"
    assert registry["services"][0]["hook"] == "patient-view"

    # 2. Test Evaluation - Normal Vitals
    patient = User(id=201, username="patient_201", hashed_password="pw", role="patient")
    db.add(patient)
    db.flush()

    obs_normal = VitalObservation(
        patient_id=201,
        systolic_bp=120.0,
        heart_rate=72.0,
        source="device"
    )
    db.add(obs_normal)
    db.commit()

    req_payload = {
        "hook": "patient-view",
        "context": {
            "userId": "Practitioner/doc-99",
            "patientId": "Patient/201"
        }
    }

    res = evaluate_cardio_risk_service(req_payload, db)
    assert "cards" in res
    assert len(res["cards"]) == 0

    # 3. Test Evaluation - High Risk Vitals (High Blood Pressure)
    obs_high = VitalObservation(
        patient_id=201,
        systolic_bp=145.0,
        heart_rate=98.0,
        source="device"
    )
    db.add(obs_high)
    db.commit()

    res_high = evaluate_cardio_risk_service(req_payload, db)
    assert len(res_high["cards"]) == 1
    card = res_high["cards"][0]
    assert card["summary"] == "Cardiovascular Risk Flagged"
    assert card["indicator"] == "warning"
    assert "Elevated systolic BP" in card["detail"]
    assert card["suggestions"][0]["actions"][0]["resource"]["resourceType"] == "ServiceRequest"

# ── FHIR Subscription webhook Tests ──────────────────────────────────────────

def test_fhir_subscription_trigger():
    clear_subscriptions()

    # 1. Register Subscription
    sub_payload = {
        "resourceType": "Subscription",
        "criteria": "Observation?code=8867-4",  # Heart rate LOINC code
        "channel": {
            "type": "rest-hook",
            "endpoint": "http://hospital-gateway.local/webhook",
            "payload": "application/fhir+json"
        }
    }

    registered = register_fhir_subscription(sub_payload)
    assert registered["id"] == "sub-1"
    assert registered["status"] == "active"
    assert len(get_active_subscriptions()) == 1

    # 2. Trigger notification dispatch - No Match (Criteria is heart rate, we pass BP)
    with patch("requests.post") as mock_post:
        dispatched = dispatch_observation_notifications(
            patient_id=202,
            observation_id=10,
            vitals_dict={"systolic_bp": 130.0}
        )
        assert dispatched == 0
        time.sleep(0.05)
        mock_post.assert_not_called()

    # 3. Trigger notification dispatch - Match (We pass heart rate)
    with patch("requests.post") as mock_post:
        mock_post.return_value = MagicMock(status_code=200)

        dispatched = dispatch_observation_notifications(
            patient_id=202,
            observation_id=11,
            vitals_dict={"heart_rate": 105.0, "systolic_bp": 142.0}
        )
        assert dispatched == 1

        # Let background thread execute
        time.sleep(0.1)

        # Verify webhook POST payload format
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        assert args[0] == "http://hospital-gateway.local/webhook"
        posted_json = kwargs["json"]
        assert posted_json["resourceType"] == "Observation"
        assert posted_json["id"] == "11"
        assert posted_json["subject"]["reference"] == "Patient/202"

# ── HIPAA AuditEvent Logging Tests ───────────────────────────────────────────

def test_hipaa_audit_event_logging():
    clear_audit_logs()

    # 1. Log a clinical access read event
    event = log_clinical_access_event(
        action="R",
        actor_id="Dr.Smith",
        patient_id=305,
        outcome_code="0",
        description="Accessed longitudinal records"
    )

    assert event["resourceType"] == "AuditEvent"
    assert event["action"] == "R"
    assert event["outcome"] == "0"
    assert event["agent"][0]["userId"]["value"] == "Dr.Smith"
    assert event["entity"][0]["what"]["reference"] == "Patient/305"
    assert "longitudinal" in event["type"]["display"]

    # 2. Verify stored in audit records list
    logs = get_logged_audit_events()
    assert len(logs) == 1
    assert logs[0]["action"] == "R"
    assert logs[0]["recorded"] is not None

    # 3. Log a failure event
    log_clinical_access_event(
        action="U",
        actor_id="UnauthorizedUser",
        patient_id=305,
        outcome_code="8",
        description="Failed attempt to update vital signs"
    )

    assert len(get_logged_audit_events()) == 2
    assert get_logged_audit_events()[1]["outcome"] == "8"
    assert get_logged_audit_events()[1]["outcomeDesc"] == "Serious Failure"
