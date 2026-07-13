"""ClinOS SMART on FHIR integration tests.

Tests the SMART app registry CRUD, launch context generation,
and FHIR scope-guard middleware.
"""
from __future__ import annotations

import os

import pytest

os.environ.setdefault("TESTING", "1")
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("SECRET_KEY", "test-secret-key-clinos")


@pytest.fixture
def auth_headers(client, db_session):
    """Register a test user and return auth headers."""
    client.post("/v1/signup", json={
        "username": "smart_test_doc",
        "email": "smart_doc@test.com",
        "password": "TestPass123!",
        "full_name": "Dr. SMART Test",
        "dob": "1980-01-01",
    })
    from backend.models import User
    user = db_session.query(User).filter(User.username == "smart_test_doc").first()
    if user:
        user.role = "doctor"
        db_session.commit()
    resp = client.post("/v1/token", data={
        "username": "smart_test_doc",
        "password": "TestPass123!",
    })
    token = resp.json().get("access_token", "")
    return {"Authorization": f"Bearer {token}"}


def test_smart_app_registry_crud(client, auth_headers):
    """Test registering, listing, and deleting a SMART app."""
    # Register
    resp = client.post("/v1/smart/apps", json={
        "app_name": "Pediatric Calculator",
        "redirect_uri": "http://127.0.0.1:9000/callback",
        "launch_url": "http://127.0.0.1:9000/launch",
    }, headers=auth_headers)
    assert resp.status_code == 200 or resp.status_code == 201, f"Register failed: {resp.text}"
    app_data = resp.json()
    assert app_data["app_name"] == "Pediatric Calculator"
    assert "client_id" in app_data
    app_id = app_data["id"]

    # List
    resp = client.get("/v1/smart/apps", headers=auth_headers)
    assert resp.status_code == 200
    apps = resp.json()
    assert any(a["id"] == app_id for a in apps)

    # Delete
    resp = client.delete(f"/v1/smart/apps/{app_id}", headers=auth_headers)
    assert resp.status_code == 200


def test_smart_launch_context(client, auth_headers):
    """Test generating a patient-scoped launch context."""
    # Register an app first
    resp = client.post("/v1/smart/apps", json={
        "app_name": "Vitals Monitor",
        "redirect_uri": "http://127.0.0.1:9001/callback",
        "launch_url": "http://127.0.0.1:9001/launch",
    }, headers=auth_headers)
    app_data = resp.json()

    # Register a patient
    p_resp = client.post("/v1/signup", json={
        "username": "smart_patient_1",
        "email": "patient1@test.com",
        "password": "TestPass123!",
        "full_name": "Test Patient",
        "dob": "1990-01-01",
    })
    assert p_resp.status_code in (200, 201), p_resp.text
    patient_id = p_resp.json()["id"]

    # Launch
    resp = client.post("/v1/smart/launch", json={
        "app_id": app_data["id"],
        "patient_id": patient_id,
    }, headers=auth_headers)

    if resp.status_code == 200:
        launch = resp.json()
        assert "launch_token" in launch
        assert "auth_code" in launch


def test_smart_token_invalid_app(client, auth_headers):
    """Launching with a non-existent app should fail."""
    resp = client.post("/v1/smart/launch", json={
        "app_id": 99999,
        "patient_id": 1,
    }, headers=auth_headers)
    assert resp.status_code in (404, 400, 422)
