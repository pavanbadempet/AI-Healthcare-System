import os
from unittest import mock

from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient
from fastapi_license_gate import LicenseManager, LicenseValidationMiddleware

SECRET_KEY = "test-secret-key-12345"
TRIAL_KEYS = {
    "TRIAL-KEY-2026": {
        "holder": "Trial Holder",
        "tier": "trial",
        "expires_at": "2030-12-31",
    },
    "EXPIRED-TRIAL-KEY": {
        "holder": "Expired Holder",
        "tier": "trial",
        "expires_at": "2020-01-01",
    },
}

manager = LicenseManager(
    secret_key=SECRET_KEY,
    trial_keys=TRIAL_KEYS,
)

app = FastAPI()
app.add_middleware(
    LicenseValidationMiddleware,
    license_manager=manager,
    exclude_paths=["/healthz", "/docs"],
    exclude_prefixes=["/public"],
)


@app.get("/healthz")
def healthz():
    return {"status": "ok"}


@app.get("/public/info")
def public_info():
    return {"info": "open access"}


@app.get("/api/dashboard")
def dashboard():
    return {"data": "secure dashboard"}


@app.get(
    "/api/community-feature",
    dependencies=[Depends(manager.enforce_license_tier("community"))],
)
def community_feature():
    return {"feature": "community stuff"}


@app.get(
    "/api/enterprise-feature",
    dependencies=[Depends(manager.enforce_license_tier("enterprise"))],
)
def enterprise_feature():
    return {"feature": "enterprise stuff"}


client = TestClient(app)


@mock.patch.dict(os.environ, {"TESTING": ""})
def test_missing_license_key():
    """Verify that a missing license key blocks the endpoint with 402."""
    with mock.patch.dict(os.environ, {"LICENSE_KEY": ""}):
        resp = client.get("/api/dashboard")
        assert resp.status_code == 402
        assert "License Key is missing" in resp.json()["detail"]


@mock.patch.dict(os.environ, {"TESTING": ""})
def test_invalid_license_key():
    """Verify that an invalid license key blocks the endpoint with 402."""
    with mock.patch.dict(os.environ, {"LICENSE_KEY": "some-junk-key"}):
        resp = client.get("/api/dashboard")
        assert resp.status_code == 402
        assert "License Key is invalid" in resp.json()["detail"]


@mock.patch.dict(os.environ, {"TESTING": ""})
def test_valid_trial_key():
    """Verify that a valid trial key allows base endpoints but blocks tier endpoints."""
    with mock.patch.dict(os.environ, {"LICENSE_KEY": "TRIAL-KEY-2026"}):
        # Base works
        resp = client.get("/api/dashboard")
        assert resp.status_code == 200

        # Community fails
        resp = client.get("/api/community-feature")
        assert resp.status_code == 402

        # Enterprise fails
        resp = client.get("/api/enterprise-feature")
        assert resp.status_code == 402


@mock.patch.dict(os.environ, {"TESTING": ""})
def test_expired_trial_key():
    """Verify that an expired trial key blocks all protected endpoints."""
    with mock.patch.dict(os.environ, {"LICENSE_KEY": "EXPIRED-TRIAL-KEY"}):
        resp = client.get("/api/dashboard")
        assert resp.status_code == 402
        assert "expired" in resp.json()["detail"]


@mock.patch.dict(os.environ, {"TESTING": ""})
def test_exclude_rules():
    """Verify that excluded routes bypass validation entirely."""
    with mock.patch.dict(os.environ, {"LICENSE_KEY": ""}):
        # Exact exclude
        assert client.get("/healthz").status_code == 200
        # Prefix exclude
        assert client.get("/public/info").status_code == 200


@mock.patch.dict(os.environ, {"TESTING": ""})
def test_community_license_key():
    """Verify that a community license key allows base & community features, but blocks enterprise."""
    key = manager.generate_license_key("Client A", "community", 30)
    with mock.patch.dict(os.environ, {"LICENSE_KEY": key}):
        # Base works
        assert client.get("/api/dashboard").status_code == 200
        # Community works
        assert client.get("/api/community-feature").status_code == 200
        # Enterprise fails
        assert client.get("/api/enterprise-feature").status_code == 402


@mock.patch.dict(os.environ, {"TESTING": ""})
def test_enterprise_license_key():
    """Verify that an enterprise license key allows all endpoints."""
    key = manager.generate_license_key("Client B", "enterprise", 30)
    with mock.patch.dict(os.environ, {"LICENSE_KEY": key}):
        assert client.get("/api/dashboard").status_code == 200
        assert client.get("/api/community-feature").status_code == 200
        assert client.get("/api/enterprise-feature").status_code == 200


@mock.patch.dict(os.environ, {"TESTING": ""})
def test_expired_cryptographic_key():
    """Verify that an expired cryptographic key is rejected."""
    key = manager.generate_license_key("Expired Client", "community", -5)
    with mock.patch.dict(os.environ, {"LICENSE_KEY": key}):
        resp = client.get("/api/dashboard")
        assert resp.status_code == 402
        assert "expired" in resp.json()["detail"]
        assert manager.get_active_license_tier() == "none"


@mock.patch.dict(os.environ, {"TESTING": "1"})
def test_testing_mode_bypass():
    """Verify that the middleware and dependency checks are bypassed when TESTING=1 is set."""
    with mock.patch.dict(os.environ, {"LICENSE_KEY": ""}):
        assert client.get("/api/dashboard").status_code == 200
        assert client.get("/api/community-feature").status_code == 200


def test_get_active_license_tier_scenarios():
    """Test get_active_license_tier directly under various edge cases."""
    # Missing license key
    with mock.patch.dict(os.environ, {"LICENSE_KEY": ""}):
        assert manager.get_active_license_tier() == "none"

    # Invalid cryptographic key
    with mock.patch.dict(os.environ, {"LICENSE_KEY": "invalid-jwt-token"}):
        assert manager.get_active_license_tier() == "none"

    # Valid trial key
    with mock.patch.dict(os.environ, {"LICENSE_KEY": "TRIAL-KEY-2026"}):
        assert manager.get_active_license_tier() == "trial"

    # Expired trial key
    with mock.patch.dict(os.environ, {"LICENSE_KEY": "EXPIRED-TRIAL-KEY"}):
        assert manager.get_active_license_tier() == "none"


def test_invalid_trial_key_expiration():
    """Verify that malformed trial key dates are handled gracefully."""
    bad_trial_keys = {
        "BAD-KEY": {
            "holder": "Bad Holder",
            "tier": "trial",
            "expires_at": "invalid-date-format",
        }
    }
    local_manager = LicenseManager(secret_key=SECRET_KEY, trial_keys=bad_trial_keys)
    is_valid, reason = local_manager.verify_license_key("BAD-KEY")
    assert not is_valid
    assert "invalid" in reason

    with mock.patch.dict(os.environ, {"LICENSE_KEY": "BAD-KEY"}):
        assert local_manager.get_active_license_tier() == "none"


@mock.patch.dict(os.environ, {"TESTING": ""})
def test_enforce_license_tier_direct():
    """Test direct dependency validation error triggers."""
    import pytest
    from fastapi import HTTPException

    # Bypassed if TESTING is set
    with mock.patch.dict(os.environ, {"TESTING": "true", "LICENSE_KEY": ""}):
        dep = manager.enforce_license_tier("community")
        dep()  # Should not raise

    # Raises 402 if license is missing
    with mock.patch.dict(os.environ, {"LICENSE_KEY": ""}):
        dep = manager.enforce_license_tier("community")
        with pytest.raises(HTTPException) as exc_info:
            dep()
        assert exc_info.value.status_code == 402
