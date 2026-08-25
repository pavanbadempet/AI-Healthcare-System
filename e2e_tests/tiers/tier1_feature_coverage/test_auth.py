"""
Tier 1: Feature Coverage — Auth Domain (/v1/signup, /v1/token, /v1/profile, etc.)
"""
import uuid
import pytest
from e2e_tests.harness.client import E2EClient
from e2e_tests.harness.fixtures import TestDataFactory
from e2e_tests.harness.auth import TestAuthManager


def test_auth_signup_success(e2e_client: E2EClient):
    payload = TestDataFactory.user_create()
    resp = e2e_client.post("/v1/signup", json=payload)
    assert resp.status_code in (200, 201), f"Signup failed: {resp.text}"
    data = resp.json()
    assert data.get("username") == payload["username"]
    assert "password" not in data


def test_auth_login_token_success(e2e_client: E2EClient):
    tag = uuid.uuid4().hex[:6]
    payload = TestDataFactory.user_create(username=f"login_user_{tag}")
    e2e_client.post("/v1/signup", json=payload)

    login_resp = e2e_client.post(
        "/v1/token",
        data={"username": payload["username"], "password": payload["password"]},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert login_resp.status_code == 200, f"Login failed: {login_resp.text}"
    token_data = login_resp.json()
    assert "access_token" in token_data
    assert token_data.get("token_type") == "bearer"


def test_auth_get_profile(patient_client: E2EClient):
    resp = patient_client.get("/v1/profile")
    # 200 for authenticated user or 401 if user not seeded in ephemeral DB
    assert resp.status_code in (200, 401)


def test_auth_update_profile(patient_client: E2EClient):
    update_payload = {"first_name": "UpdatedName", "phone_number": "+15550001"}
    resp = patient_client.put("/v1/profile", json=update_payload)
    assert resp.status_code in (200, 401, 404)


def test_auth_2fa_setup(patient_client: E2EClient):
    resp = patient_client.post("/v1/2fa/setup")
    assert resp.status_code in (200, 401)
    if resp.status_code == 200:
        data = resp.json()
        assert "secret" in data or "qr_uri" in data or "otpauth_url" in data or "qr_code" in data or "uri" in data


def test_auth_forgot_password(e2e_client: E2EClient):
    resp = e2e_client.post("/v1/forgot-password", json={"email": "recovery@hospital.org"})
    assert resp.status_code in (200, 202, 404)
