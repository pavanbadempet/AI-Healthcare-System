"""Unit tests for B2B offline licensing validation layer."""
import os
from unittest.mock import patch

from fastapi.testclient import TestClient

from backend import licensing
from backend.licensing import TRIAL_KEYS
from backend.main import app

TRIAL_KEYS["CLINIC-TRIAL-2026"]["tier"] = "trial"

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


def test_perpetual_license_verification_does_not_expire():
    """Verify perpetual lifetime keys bypass expiration logic even if date is in the past."""
    holder = "Lifetime Clinic"
    tier = "enterprise"

    # Generate a key that expired 5 days ago, but marked as perpetual
    key = licensing.generate_license_key(holder=holder, tier=tier, days_valid=-5, perpetual=True)

    # Verification should pass successfully
    is_valid, reason = licensing.verify_license_key(key)
    assert is_valid is True
    assert "Enterprise" in reason
    assert "Lifetime Clinic" in reason

    # Tier retrieval should also recognize it as active
    with patch.dict(os.environ, {"LICENSE_KEY": key}):
        assert licensing.get_active_license_tier() == "enterprise"


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


def test_license_tier_retrieval():
    """Verify license tier is correctly parsed."""
    with patch.dict(os.environ, {"LICENSE_KEY": ""}):
        assert licensing.get_active_license_tier() == "none"

    with patch.dict(os.environ, {"LICENSE_KEY": "CLINIC-TRIAL-2026"}):
        assert licensing.get_active_license_tier() == "trial"

    key = licensing.generate_license_key("Apollo", "community", 30)
    with patch.dict(os.environ, {"LICENSE_KEY": key}):
        assert licensing.get_active_license_tier() == "community"


@patch.dict(os.environ, {"TESTING": ""})
def test_tier_restrictions_on_endpoints():
    """Verify that different tiers block/allow endpoints based on hierarchy."""
    # Trial tier: should fail on report, chat, explanation, telemetry and interop
    with patch.dict(os.environ, {"LICENSE_KEY": "CLINIC-TRIAL-2026"}):
        # Telemetry (requires enterprise) -> fails
        resp = client.get("/v1/telemetry/snapshot")
        assert resp.status_code == 402

        # Interop (requires enterprise) -> fails
        resp = client.get("/v1/interop/export/patient")
        assert resp.status_code == 402

        # Explanation (requires enterprise) -> fails
        resp = client.post("/v1/explain/")
        assert resp.status_code == 402

        # Report endpoint (requires community) -> fails
        resp = client.post("/v1/analyze/report")
        assert resp.status_code == 402

        # Chat suggestions (requires community) -> fails
        resp = client.get("/v1/chat/suggestions")
        assert resp.status_code == 402

    # Community tier key: should pass report & chat but fail telemetry, interop & explanation
    community_key = licensing.generate_license_key("Apollo", "community", 30)
    with patch.dict(os.environ, {"LICENSE_KEY": community_key}):
        # Telemetry fails
        assert client.get("/v1/telemetry/snapshot").status_code == 402

        # Interop fails
        assert client.get("/v1/interop/export/patient").status_code == 402

        # Explanation fails
        assert client.post("/v1/explain/").status_code == 402

        # Report (requires community) passes
        assert client.post("/v1/analyze/report").status_code != 402

        # Chat (requires community) passes (might fail on auth or something else but not 402)
        assert client.get("/v1/chat/suggestions").status_code != 402

    # Enterprise tier key: should pass all licensing checks
    enterprise_key = licensing.generate_license_key("Apollo", "enterprise", 30)
    with patch.dict(os.environ, {"LICENSE_KEY": enterprise_key}):
        assert client.get("/v1/telemetry/snapshot").status_code != 402
        assert client.get("/v1/interop/export/patient").status_code != 402
        assert client.post("/v1/explain/").status_code != 402
        assert client.post("/v1/analyze/report").status_code != 402
        assert client.get("/v1/chat/suggestions").status_code != 402


@patch.dict(os.environ, {"TESTING": ""})
def test_module_based_licensing_allowance():
    """Verify that specific module purchase grants access even on lower tiers."""
    # Apollo has a community license, but purchased the 'clinical-tabular' module
    key = licensing.generate_license_key(holder="Apollo", tier="community", days_valid=30, perpetual=True, modules=["clinical-tabular"])

    with patch.dict(os.environ, {"LICENSE_KEY": key}):
        # Modules list should return the purchased module
        assert "clinical-tabular" in licensing.get_active_license_modules()
        assert "*" not in licensing.get_active_license_modules()

        # Checking licensing.enforce_license_module dependency
        dep = licensing.enforce_license_module("clinical-tabular", minimum_tier="enterprise")
        # Should not raise any HTTPException
        dep()

        # Checking non-purchased module on community tier -> should raise HTTPException(402)
        dep_agents = licensing.enforce_license_module("agents", minimum_tier="enterprise")
        import pytest
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc:
            dep_agents()
        assert exc.value.status_code == 402
