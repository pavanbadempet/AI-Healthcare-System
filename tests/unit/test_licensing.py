"""Unit tests for B2B offline licensing validation layer."""
import os
from unittest.mock import patch

from fastapi.testclient import TestClient

from backend import licensing
from backend.main import app

client = TestClient(app)


def test_license_key_generation_and_verification():
    """Verify license keys can be generated and verified cryptographically."""
    holder = "Apollo Hospital"
    tier = "enterprise"

    # Generate signed key
    key = licensing.generate_license_key(holder=holder, tier=tier, days_valid=30)
    assert isinstance(key, str)
    assert len(key) > 0

    # Verify key
    is_valid, reason = licensing.verify_license_key(key)
    assert is_valid is True
    assert "Enterprise" in reason
    assert "Apollo Hospital" in reason


def test_license_trial_fallback():
    """Verify standard trial key is recognized."""
    is_valid, reason = licensing.verify_license_key("CLINIC-TRIAL-2026")
    assert is_valid is True
    assert "Trial" in reason


def test_license_invalid_verification():
    """Verify invalid keys fail verification."""
    is_valid, reason = licensing.verify_license_key("INVALID-KEY-12345")
    assert is_valid is False
    assert "signature" in reason.lower()


@patch.dict(os.environ, {"TESTING": ""})
def test_endpoints_blocked_when_license_missing():
    """Verify endpoints return 402 when LICENSE_KEY is missing."""
    with patch.dict(os.environ, {"LICENSE_KEY": ""}):
        resp = client.get("/v1/profile")
        assert resp.status_code == 402
        assert "License Key is missing" in resp.json()["detail"]


@patch.dict(os.environ, {"TESTING": ""})
def test_endpoints_blocked_when_license_invalid():
    """Verify endpoints return 402 when LICENSE_KEY is invalid."""
    with patch.dict(os.environ, {"LICENSE_KEY": "INVALID-LICENSE-KEY"}):
        resp = client.get("/v1/profile")
        assert resp.status_code == 402
        assert "invalid or expired" in resp.json()["detail"].lower()


@patch.dict(os.environ, {"TESTING": ""})
def test_unprotected_endpoints_pass_without_license():
    """Verify healthcheck and authentication paths pass even without license."""
    with patch.dict(os.environ, {"LICENSE_KEY": ""}):
        resp = client.get("/healthz")
        assert resp.status_code == 200
