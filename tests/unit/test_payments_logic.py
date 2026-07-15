"""
Tests for payments.py — plan catalog, credential loading, order validation,
endpoint auth, and error handling.
"""
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException
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

def _auth(client, username="pay_user"):
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

# ── get_plan_config ───────────────────────────────────────────────────────────

def test_get_plan_config_returns_pro():
    plan = payments.get_plan_config("pro")
    assert plan["amount_inr"] == 99900
    assert plan["amount_usd"] == 999
    assert plan["tier"] == "pro"

def test_get_plan_config_returns_enterprise():
    plan = payments.get_plan_config("enterprise")
    assert plan["amount_inr"] == 249900
    assert plan["tier"] == "clinic"

def test_get_plan_config_alias_pro_monthly():
    plan = payments.get_plan_config("pro_monthly")
    assert plan["tier"] == "pro"

def test_get_plan_config_alias_clinic():
    plan = payments.get_plan_config("clinic")
    assert plan["tier"] == "clinic"

def test_get_plan_config_raises_400_for_unknown():
    with pytest.raises(HTTPException) as exc:
        payments.get_plan_config("unknown_plan")
    assert exc.value.status_code == 400

# ── create_order ─────────────────────────────────────────────────────────────

def test_create_order_returns_order_data(client):
    headers = _auth(client)
    with patch("backend.payments.ACTIVE_GATEWAY", "razorpay"), \
         patch("backend.payments._testing_enabled", return_value=True), \
         patch("backend.payments.RAZORPAY_KEY_ID", "rzp_test_placeholder"), \
         patch("backend.payments.razorpay_client", MagicMock()):
        r = client.post("/payments/create-order", json={"plan_id": "pro"}, headers=headers)
        assert r.status_code == 200
        data = r.json()
        assert data["gateway"] == "razorpay"
        assert data["id"] == "order_test_12345"
        assert data["amount"] == 99900
        assert data["currency"] == "INR"

def test_create_order_returns_400_for_invalid_plan(client):
    headers = _auth(client)
    r = client.post("/payments/create-order", json={"plan_id": "unknown"}, headers=headers)
    assert r.status_code == 400

def test_create_order_returns_503_when_no_gateway(client):
    headers = _auth(client)
    with patch("backend.payments.ACTIVE_GATEWAY", "razorpay"), \
         patch("backend.payments.razorpay_client", None):
        r = client.post("/payments/create-order", json={"plan_id": "pro"}, headers=headers)
        assert r.status_code == 503

# ── verify_payment ───────────────────────────────────────────────────────────

def test_verify_payment_returns_success_and_upgrades_tier(client, db_session):
    headers = _auth(client, "verify_user")
    
    with patch("backend.payments.ACTIVE_GATEWAY", "razorpay"), \
         patch("backend.payments._testing_enabled", return_value=True), \
         patch("backend.payments.RAZORPAY_KEY_ID", "rzp_test_placeholder"), \
         patch("backend.payments.razorpay_client", MagicMock()):
        r = client.post("/payments/verify", json={
            "gateway": "razorpay",
            "razorpay_order_id": "order_1",
            "razorpay_payment_id": "pay_1",
            "razorpay_signature": "sig_1",
            "plan_id": "pro"
        }, headers=headers)
        assert r.status_code == 200
        data = r.json()
        assert data["success"] is True
        assert data["tier"] == "pro"

def test_verify_payment_returns_400_on_bad_signature(client):
    headers = _auth(client, "sig_user")
    mock_client = MagicMock()
    mock_client.utility.verify_payment_signature.side_effect = payments.razorpay.errors.SignatureVerificationError("bad", "bad")
    
    with patch("backend.payments.ACTIVE_GATEWAY", "razorpay"), \
         patch("backend.payments._testing_enabled", return_value=False), \
         patch("backend.payments.RAZORPAY_KEY_ID", "real_key"), \
         patch("backend.payments.razorpay_client", mock_client):
        r = client.post("/payments/verify", json={
            "gateway": "razorpay",
            "razorpay_order_id": "order_1",
            "razorpay_payment_id": "pay_1",
            "razorpay_signature": "sig_bad",
            "plan_id": "pro"
        }, headers=headers)
        assert r.status_code == 400
        assert "Invalid payment signature" in r.text
