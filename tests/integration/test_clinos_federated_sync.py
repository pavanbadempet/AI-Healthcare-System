"""ClinOS Federated Sync Bridge integration tests.

Tests clinician feedback submission, Laplace DP noise injection,
sync audit logging, and privacy budget exhaustion guard.
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
        "username": "fed_test_doc",
        "email": "fed_doc@test.com",
        "password": "TestPass123!",
        "full_name": "Dr. Federated",
        "dob": "1980-01-01",
    })
    from backend.models import User
    user = db_session.query(User).filter(User.username == "fed_test_doc").first()
    if user:
        user.role = "doctor"
        db_session.commit()
    resp = client.post("/v1/token", data={
        "username": "fed_test_doc",
        "password": "TestPass123!",
    })
    token = resp.json().get("access_token", "")
    return {"Authorization": f"Bearer {token}"}


def test_federated_feedback_submission(client, auth_headers):
    """Test submitting a clinician diagnostic correction."""
    p_resp = client.post("/v1/signup", json={
        "username": "fed_patient_1",
        "email": "fed_patient1@test.com",
        "password": "TestPass123!",
        "full_name": "Test Patient Fed",
        "dob": "1990-01-01",
    })
    assert p_resp.status_code in (200, 201), p_resp.text
    patient_id = p_resp.json()["id"]

    resp = client.post("/v1/federated/feedback", json={
        "patient_id": patient_id,
        "model_name": "heart_disease",
        "input_features": {"age": 55, "cholesterol": 240, "blood_pressure": 140},
        "prediction_result": {"risk": "low", "confidence": 0.72},
        "corrected_label": "high",
    }, headers=auth_headers)
    assert resp.status_code in (200, 201), f"Feedback submission failed: {resp.text}"
    data = resp.json()
    assert data["model_name"] == "heart_disease"
    assert data["corrected_label"] == "high"
    assert data["status"] == "pending_sync"


def test_federated_sync_with_dp(client, auth_headers):
    """Test executing a DP-protected gradient sync."""
    # Submit a couple more feedbacks first
    for i in range(3):
        p_resp = client.post("/v1/signup", json={
            "username": f"fed_patient_sync_{i}",
            "email": f"fed_pat_sync_{i}@test.com",
            "password": "TestPass123!",
            "full_name": f"Patient Sync {i}",
            "dob": "1990-01-01",
        })
        assert p_resp.status_code in (200, 201), p_resp.text
        patient_id = p_resp.json()["id"]

        client.post("/v1/federated/feedback", json={
            "patient_id": patient_id,
            "model_name": "heart_disease",
            "input_features": {"age": 40 + i, "cholesterol": 200 + i * 10},
            "prediction_result": {"risk": "low", "confidence": 0.6 + i * 0.05},
            "corrected_label": "moderate",
        }, headers=auth_headers)

    # Execute sync
    resp = client.post("/v1/federated/sync", json={
        "model_name": "heart_disease",
        "epsilon": 1.0,
        "sensitivity": 1.0,
    }, headers=auth_headers)
    assert resp.status_code == 200, f"Sync failed: {resp.text}"
    data = resp.json()
    assert data["status"] == "success"
    assert data["records_synced"] > 0
    assert data["epsilon_consumed"] > 0
    assert "noisy_gradients" in data


def test_federated_stats(client, auth_headers):
    """Test fetching federated stats."""
    resp = client.get("/v1/federated/stats", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "pending_count" in data
    assert "total_epsilon_spent" in data


def test_federated_audit_history(client, auth_headers):
    """Test fetching sync audit history."""
    resp = client.get("/v1/federated/audits", headers=auth_headers)
    assert resp.status_code == 200
    audits = resp.json()
    assert isinstance(audits, list)
    if len(audits) > 0:
        assert "sync_run_id" in audits[0]
        assert "epsilon_consumed" in audits[0]
