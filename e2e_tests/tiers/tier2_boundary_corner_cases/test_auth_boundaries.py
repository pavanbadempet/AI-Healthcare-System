"""
Tier 2: Boundary & Corner Cases — Authentication & Token Security
"""
import uuid
import pytest
from e2e_tests.harness.client import E2EClient
from e2e_tests.harness.fixtures import TestDataFactory


def test_auth_unauthenticated_profile_access(e2e_client: E2EClient):
    resp = e2e_client.get("/v1/profile")
    assert resp.status_code == 401, f"Expected 401 Unauthorized, got {resp.status_code}"


def test_auth_invalid_token_header(e2e_client: E2EClient):
    resp = e2e_client.get("/v1/profile", headers={"Authorization": "Bearer invalid.jwt.token"})
    assert resp.status_code == 401, f"Expected 401 Unauthorized, got {resp.status_code}"


def test_auth_malformed_auth_header(e2e_client: E2EClient):
    resp = e2e_client.get("/v1/profile", headers={"Authorization": "NotBearer header"})
    assert resp.status_code == 401, f"Expected 401 Unauthorized, got {resp.status_code}"


def test_auth_duplicate_username_signup(e2e_client: E2EClient):
    username = f"dup_user_{uuid.uuid4().hex[:6]}"
    payload = TestDataFactory.user_create(username=username)
    # First signup
    e2e_client.post("/v1/signup", json=payload)
    # Duplicate signup attempt
    resp2 = e2e_client.post("/v1/signup", json=payload)
    assert resp2.status_code in (400, 409, 422), f"Expected duplicate error, got {resp2.status_code}"


def test_auth_login_invalid_password(e2e_client: E2EClient):
    resp = e2e_client.post(
        "/v1/token",
        data={"username": "non_existent_user_9999", "password": "WrongPassword999!"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert resp.status_code in (400, 401, 404, 422), f"Expected auth failure, got {resp.status_code}"


def test_auth_signup_empty_body(e2e_client: E2EClient):
    resp = e2e_client.post("/v1/signup", json={})
    assert resp.status_code in (400, 422), f"Expected validation error, got {resp.status_code}"
