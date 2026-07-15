"""
Security tests for payments.py — ensuring server-side pricing, signature verification,
and error redaction.
"""
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend import payments
from backend.database import Base, get_db
from backend.main import app
from backend.prediction import initialize_models

# ── DB + client ───────────────────────────────────────────────────────────────

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def _auth(client, username="pay_sec_user"):
    pwd = "PayTest123!"
    client.post("/signup", json={
        "username": username, "password": pwd,
        "email": f"{username}@test.com", "full_name": "Pay", "dob": "1990-01-01",
    })
    r = client.post("/token", data={"username": username, "password": pwd})
    return {"Authorization": f"Bearer {r.json()['access_token']}"}

@pytest.fixture
def db_session():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

@pytest.fixture
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            db_session.close()
    app.dependency_overrides[get_db] = override_get_db
    initialize_models()
    with TestClient(app, base_url="http://127.0.0.1") as c:
        yield c
    app.dependency_overrides.clear()

# ── Tests ────────────────────────────────────────────────────────────────────

def test_verify_payment_rejects_order_for_different_user(client, db_session):
    headers = _auth(client, "user_one")
    
    # We pretend the stripe session metadata belongs to user_id "999" (not current_user)
    mock_session = MagicMock()
    mock_session.payment_status = "paid"
    mock_session.metadata = {"user_id": "999", "plan": "pro"}

    with patch("backend.payments.ACTIVE_GATEWAY", "stripe"), \
         patch("backend.payments.stripe.api_key", "sk_live_123"), \
         patch("backend.payments.stripe.checkout.Session.retrieve", return_value=mock_session):
        r = client.post("/payments/verify", json={
            "gateway": "stripe",
            "payment_intent_id": "cs_123",
            "plan_id": "pro"
        }, headers=headers)
        assert r.status_code == 403
        assert "Order does not belong to current user" in r.text

def test_create_order_hides_gateway_error_details(client):
    headers = _auth(client)
    sensitive_err = "Internal Razorpay Error token=secret"
    
    mock_client = MagicMock()
    mock_client.order.create.side_effect = Exception(sensitive_err)
    
    with patch("backend.payments.ACTIVE_GATEWAY", "razorpay"), \
         patch("backend.payments.razorpay_client", mock_client):
        r = client.post("/payments/create-order", json={"plan_id": "pro"}, headers=headers)
        assert r.status_code == 500
        assert "Failed to create payment order" in r.text
        assert sensitive_err not in r.text

def test_verify_payment_hides_gateway_error_details(client):
    headers = _auth(client)
    sensitive_err = "Internal Stripe Error token=secret"
    
    with patch("backend.payments.ACTIVE_GATEWAY", "stripe"), \
         patch("backend.payments.stripe.api_key", "sk_live_123"), \
         patch("backend.payments.stripe.checkout.Session.retrieve", side_effect=Exception(sensitive_err)):
        r = client.post("/payments/verify", json={
            "gateway": "stripe",
            "payment_intent_id": "cs_123",
            "plan_id": "pro"
        }, headers=headers)
        assert r.status_code == 500
        assert "Failed to verify payment" in r.text
        assert sensitive_err not in r.text

def test_create_order_rejects_unknown_plan(client):
    headers = _auth(client)
    r = client.post("/payments/create-order", json={"plan_id": "hacker_plan"}, headers=headers)
    assert r.status_code == 400
    assert "Invalid payment plan" in r.text
