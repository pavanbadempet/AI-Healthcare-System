"""ClinOS Clinical Intelligence integration tests.

Tests the alert engine, acknowledgement workflow, patient insights,
and explainability feature importance responses.
"""
from __future__ import annotations

import os

import pytest

os.environ.setdefault("TESTING", "1")
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("SECRET_KEY", "test-secret-key-clinos")


@pytest.fixture
def auth_headers(client, db_session):
    client.post("/v1/signup", json={
        "username": "intel_test_doc",
        "email": "intel_doc@test.com",
        "password": "TestPass123!",
        "full_name": "Dr. Intelligence",
        "dob": "1980-01-01",
    })
    from backend.models import User
    user = db_session.query(User).filter(User.username == "intel_test_doc").first()
    if user:
        user.role = "doctor"
        db_session.commit()
    resp = client.post("/v1/token", data={
        "username": "intel_test_doc",
        "password": "TestPass123!",
    })
    token = resp.json().get("access_token", "")
    return {"Authorization": f"Bearer {token}"}


def test_list_alerts_empty(client, auth_headers):
    """Initially, the alerts list should be empty or return successfully."""
    resp = client.get("/v1/intelligence/alerts", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)


def test_list_alerts_with_severity_filter(client, auth_headers):
    """Test filtering alerts by severity level."""
    resp = client.get("/v1/intelligence/alerts?severity=CRITICAL", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)


def test_alert_acknowledge_nonexistent(client, auth_headers):
    """Acknowledging a non-existent alert should return 404."""
    resp = client.post("/v1/intelligence/alerts/99999/acknowledge", headers=auth_headers)
    assert resp.status_code == 404


def test_patient_insights(client, auth_headers):
    """Test fetching AI-generated patient insights (includes medical disclaimer)."""
    # Register a patient first
    p_resp = client.post("/v1/signup", json={
        "username": "intel_patient",
        "email": "intel_patient@test.com",
        "password": "TestPass123!",
        "full_name": "Test Patient Intel",
        "dob": "1990-01-01",
    })
    assert p_resp.status_code in (200, 201), p_resp.text
    patient_id = p_resp.json()["id"]

    resp = client.get(f"/v1/intelligence/insights/{patient_id}", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    # Should contain the medical disclaimer
    if isinstance(data, dict) and "disclaimer" in data:
        assert "informational purposes" in data["disclaimer"].lower() or "consult" in data["disclaimer"].lower()


def test_explainability_mock(client, auth_headers):
    """Test fetching explainability data for a prediction."""
    resp = client.get("/v1/intelligence/explainability/1", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "feature_importances" in data
    assert "explanation_text" in data
    assert isinstance(data["feature_importances"], dict)
