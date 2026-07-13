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
    assert plan["amount"] == 99900
    assert plan["currency"] == "INR"
    assert plan["tier"] == "pro"


def test_get_plan_config_returns_enterprise():
    plan = payments.get_plan_config("enterprise")
    assert plan["amount"] == 249900
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


# ── load_razorpay_credentials ─────────────────────────────────────────────────

def test_load_razorpay_credentials_returns_none_when_not_set(monkeypatch):
    monkeypatch.delenv("RAZORPAY_KEY_ID", raising=False)
    monkeypatch.delenv("RAZORPAY_KEY_SECRET", raising=False)
    monkeypatch.setenv("TESTING", "")
    key_id, key_secret = payments.load_razorpay_credentials()
    assert key_id is None
    assert key_secret is None


def test_load_razorpay_credentials_returns_test_placeholders_in_testing(monkeypatch):
    monkeypatch.delenv("RAZORPAY_KEY_ID", raising=False)
    monkeypatch.delenv("RAZORPAY_KEY_SECRET", raising=False)
    monkeypatch.setenv("TESTING", "1")
    key_id, key_secret = payments.load_razorpay_credentials()
    assert key_id == "rzp_test_placeholder"
    assert key_secret == "secret_placeholder"


def test_load_razorpay_credentials_uses_env_vars(monkeypatch):
    monkeypatch.setenv("RAZORPAY_KEY_ID", "rzp_live_abc123")
    monkeypatch.setenv("RAZORPAY_KEY_SECRET", "live_secret_xyz")
    key_id, key_secret = payments.load_razorpay_credentials()
    assert key_id == "rzp_live_abc123"
    assert key_secret == "live_secret_xyz"


# ── get_payment_client ────────────────────────────────────────────────────────

def test_get_payment_client_raises_503_when_none():
    with patch("backend.payments.client", None):
        with pytest.raises(HTTPException) as exc:
            payments.get_payment_client()
    assert exc.value.status_code == 503


def test_get_payment_client_returns_client_when_set():
    mock_client = MagicMock()
    with patch("backend.payments.client", mock_client):
        result = payments.get_payment_client()
    assert result is mock_client


# ── validate_order_for_user ───────────────────────────────────────────────────

def _make_user(user_id=1):
    u = MagicMock()
    u.id = user_id
    return u


def test_validate_order_for_user_valid_pro_order():
    user = _make_user(1)
    order = {
        "notes": {"user_id": "1", "plan": "pro"},
        "amount": 99900,
        "currency": "INR",
    }
    plan = payments.validate_order_for_user(order, user)
    assert plan["tier"] == "pro"


def test_validate_order_for_user_raises_403_wrong_user():
    user = _make_user(99)
    order = {
        "notes": {"user_id": "1", "plan": "pro"},
        "amount": 99900,
        "currency": "INR",
    }
    with pytest.raises(HTTPException) as exc:
        payments.validate_order_for_user(order, user)
    assert exc.value.status_code == 403


def test_validate_order_for_user_raises_400_amount_mismatch():
    user = _make_user(1)
    order = {
        "notes": {"user_id": "1", "plan": "pro"},
        "amount": 50000,  # wrong amount
        "currency": "INR",
    }
    with pytest.raises(HTTPException) as exc:
        payments.validate_order_for_user(order, user)
    assert exc.value.status_code == 400


def test_validate_order_for_user_raises_400_invalid_amount_type():
    user = _make_user(1)
    order = {
        "notes": {"user_id": "1", "plan": "pro"},
        "amount": "not_a_number",
        "currency": "INR",
    }
    with pytest.raises(HTTPException) as exc:
        payments.validate_order_for_user(order, user)
    assert exc.value.status_code == 400


def test_validate_order_for_user_raises_400_currency_mismatch():
    user = _make_user(1)
    order = {
        "notes": {"user_id": "1", "plan": "pro"},
        "amount": 99900,
        "currency": "USD",  # wrong currency
    }
    with pytest.raises(HTTPException) as exc:
        payments.validate_order_for_user(order, user)
    assert exc.value.status_code == 400


# ── /payments/create-order ────────────────────────────────────────────────────

def test_create_order_requires_auth(client):
    resp = client.post("/payments/create-order", json={"plan_id": "pro"})
    assert resp.status_code == 401


def test_create_order_returns_order_data(client):
    headers = _auth(client, "pay_create")
    mock_order = {
        "id": "order_test_123",
        "amount": 99900,
        "currency": "INR",
        "status": "created",
    }
    mock_client = MagicMock()
    mock_client.order.create.return_value = mock_order

    with patch("backend.payments.get_payment_client", return_value=mock_client):
        resp = client.post("/payments/create-order",
                           json={"plan_id": "pro"}, headers=headers)

    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == "order_test_123"
    assert "amount" in data
    assert "plan_id" in data


def test_create_order_returns_503_when_no_gateway(client):
    headers = _auth(client, "pay_no_gw")
    with patch("backend.payments.client", None):
        resp = client.post("/payments/create-order",
                           json={"plan_id": "pro"}, headers=headers)
    assert resp.status_code == 503


def test_create_order_returns_400_for_invalid_plan(client):
    headers = _auth(client, "pay_bad_plan")
    mock_client = MagicMock()
    with patch("backend.payments.get_payment_client", return_value=mock_client):
        resp = client.post("/payments/create-order",
                           json={"plan_id": "nonexistent"}, headers=headers)
    assert resp.status_code == 400


# ── /payments/verify ──────────────────────────────────────────────────────────

def test_verify_payment_requires_auth(client):
    resp = client.post("/payments/verify", json={
        "razorpay_order_id": "o1",
        "razorpay_payment_id": "p1",
        "razorpay_signature": "s1",
    })
    assert resp.status_code == 401


def test_verify_payment_returns_success_and_upgrades_tier(client, db_session):
    headers = _auth(client, "pay_verify")

    # Get the numeric user ID directly from the DB
    from backend.models import User
    user = db_session.query(User).filter_by(username="pay_verify").first()
    user_id = str(user.id)

    mock_order = {
        "notes": {"user_id": user_id, "plan": "pro"},
        "amount": 99900,
        "currency": "INR",
    }
    mock_client = MagicMock()
    mock_client.utility.verify_payment_signature.return_value = True
    mock_client.order.fetch.return_value = mock_order

    with patch("backend.payments.get_payment_client", return_value=mock_client):
        resp = client.post("/payments/verify", json={
            "razorpay_order_id": "order_123",
            "razorpay_payment_id": "pay_123",
            "razorpay_signature": "sig_123",
            "plan_id": "pro",
        }, headers=headers)

    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert data["tier"] == "pro"


def test_verify_payment_returns_400_on_bad_signature(client):
    import razorpay
    headers = _auth(client, "pay_badsig")
    mock_client = MagicMock()
    mock_client.utility.verify_payment_signature.side_effect = \
        razorpay.errors.SignatureVerificationError("bad sig", "field")

    with patch("backend.payments.get_payment_client", return_value=mock_client):
        resp = client.post("/payments/verify", json={
            "razorpay_order_id": "o1",
            "razorpay_payment_id": "p1",
            "razorpay_signature": "bad",
        }, headers=headers)

    assert resp.status_code == 400
    assert "Signature" in resp.json()["detail"]
