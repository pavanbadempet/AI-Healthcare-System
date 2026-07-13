import hashlib
import hmac
import json
import os
import sys
from unittest import mock

from fastapi.testclient import TestClient

# Add repository root to python path to import keygen_server
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))
from scripts.keygen_server import app

client = TestClient(app)


def test_health():
    """Verify that keygen health endpoint is alive."""
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["service"] == "keygen-server"


def test_manual_generate_unauthorized():
    """Verify that manual key generation is blocked without proper API key."""
    resp = client.post(
        "/manual-generate",
        json={"holder": "Test Clinic", "tier": "community", "days_valid": 30},
        headers={"X-API-Key": "wrong-key"},
    )
    assert resp.status_code == 401


def test_manual_generate_authorized():
    """Verify that manual key generation works with valid API key."""
    with mock.patch("scripts.keygen_server.ADMIN_API_KEY", "test-admin-secret"):
        resp = client.post(
            "/manual-generate",
            json={"holder": "Hospital Alpha", "tier": "enterprise", "days_valid": 10},
            headers={"X-API-Key": "test-admin-secret"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["holder"] == "Hospital Alpha"
        assert data["tier"] == "enterprise"
        assert "license_key" in data


def test_lemonsqueezy_webhook_invalid_signature():
    """Verify that invalid webhook signatures are rejected with 401."""
    with mock.patch("scripts.keygen_server.LEMONSQUEEZY_WEBHOOK_SECRET", "webhook-secret"):
        resp = client.post(
            "/webhook/lemonsqueezy",
            json={"meta": {"event_name": "order_created"}},
            headers={"X-Signature": "wrong-hash"},
        )
        assert resp.status_code == 401


def test_lemonsqueezy_webhook_valid_signature_order_created():
    """Verify that a valid LemonSqueezy order created event issues a license key."""
    secret = "my-secure-webhook-secret-2026"
    body_data = {
        "meta": {"event_name": "order_created"},
        "data": {
            "attributes": {
                "variant_id": "variant_comm_123",
                "customer_name": "Dr. Smith",
                "customer_email": "smith@clinic.com",
            }
        },
    }
    body_bytes = json.dumps(body_data).encode("utf-8")

    # Calculate correct signature hash
    signature = hmac.new(secret.encode("utf-8"), body_bytes, hashlib.sha256).hexdigest()

    with mock.patch("scripts.keygen_server.LEMONSQUEEZY_WEBHOOK_SECRET", secret):
        resp = client.post(
            "/webhook/lemonsqueezy",
            content=body_bytes,
            headers={"X-Signature": signature, "Content-Type": "application/json"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "success"
        assert data["issued_to"] == "Dr. Smith"
        assert data["email"] == "smith@clinic.com"
        assert data["tier"] == "community"
        assert "license_key" in data
