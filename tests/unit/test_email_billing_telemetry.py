"""
Tests for email_service.py, billing.py, and telemetry.py.
"""
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend import billing, email_service, models, telemetry
from backend.database import Base, get_db
from backend.main import app
from backend.prediction import initialize_models

# ── DB + client ───────────────────────────────────────────────────────────────

engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


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


def _auth(client, username, role="patient"):
    pwd = "TestPass123!"
    client.post("/signup", json={
        "username": username, "password": pwd,
        "email": f"{username}@test.com", "full_name": username.title(), "dob": "1990-01-01",
    })
    r = client.post("/token", data={"username": username, "password": pwd})
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def _set_role(db_session, username, role):
    u = db_session.query(models.User).filter_by(username=username).first()
    if u:
        u.role = role
        db_session.commit()


def _get_id(db_session, username):
    u = db_session.query(models.User).filter_by(username=username).first()
    return u.id if u else None


# ══════════════════════════════════════════════════════════════════════
# EMAIL SERVICE
# ══════════════════════════════════════════════════════════════════════

def test_send_booking_confirmation_returns_true_in_simulation(monkeypatch):
    monkeypatch.delenv("SMTP_SERVER", raising=False)
    result = email_service.send_booking_confirmation(
        to_email="patient@example.com",
        patient_name="Jane Doe",
        doctor_name="Dr. Smith",
        date_time="2099-06-01 10:00",
        link="https://meet.jit.si/test",
    )
    assert result is True


def test_send_booking_confirmation_logs_when_no_smtp(monkeypatch, caplog):
    monkeypatch.delenv("SMTP_SERVER", raising=False)
    import logging
    with caplog.at_level(logging.INFO, logger="backend.email_service"):
        email_service.send_booking_confirmation(
            to_email="test@example.com",
            patient_name="Test",
            doctor_name="Dr. Test",
            date_time="2099-01-01",
            link="https://example.com",
        )
    assert "simulated" in caplog.text.lower()


def test_send_booking_confirmation_returns_false_on_smtp_error(monkeypatch):
    monkeypatch.setenv("SMTP_SERVER", "smtp.example.com")
    monkeypatch.setenv("SMTP_EMAIL", "noreply@example.com")
    with patch("smtplib.SMTP", side_effect=Exception("connection refused")):
        result = email_service.send_booking_confirmation(
            to_email="patient@example.com",
            patient_name="Jane",
            doctor_name="Dr. Smith",
            date_time="2099-01-01",
            link="https://example.com",
        )
    assert result is False


def test_send_booking_confirmation_does_not_log_pii(monkeypatch, caplog):
    """Patient name and email should not appear in error logs."""
    monkeypatch.setenv("SMTP_SERVER", "smtp.example.com")
    monkeypatch.setenv("SMTP_EMAIL", "noreply@example.com")
    import logging
    with caplog.at_level(logging.ERROR, logger="backend.email_service"), \
         patch("smtplib.SMTP", side_effect=Exception("error")):
        email_service.send_booking_confirmation(
            to_email="secret-patient@hospital.com",
            patient_name="John Secret",
            doctor_name="Dr. Private",
            date_time="2099-01-01",
            link="https://example.com",
        )
    assert "secret-patient@hospital.com" not in caplog.text
    assert "John Secret" not in caplog.text


# ══════════════════════════════════════════════════════════════════════
# BILLING — helper logic
# ══════════════════════════════════════════════════════════════════════

def test_is_billing_staff_true_for_billing_role():
    u = MagicMock()
    u.role = "billing"
    assert billing._is_billing_staff(u) is True


def test_is_billing_staff_false_for_patient():
    u = MagicMock()
    u.role = "patient"
    assert billing._is_billing_staff(u) is False


def test_require_billing_or_admin_raises_for_patient():
    u = MagicMock()
    u.role = "patient"
    with patch("backend.billing.auth.is_admin", return_value=False):
        with pytest.raises(HTTPException) as exc:
            billing._require_billing_or_admin(u)
    assert exc.value.status_code == 403


def test_require_billing_or_admin_passes_for_admin():
    u = MagicMock()
    u.role = "admin"
    with patch("backend.billing.auth.is_admin", return_value=True):
        billing._require_billing_or_admin(u)  # Should not raise


def test_round_money_rounds_to_2_decimal_places():
    assert billing._round_money(10.5051) == 10.51
    assert billing._round_money(100.001) == 100.0
    assert billing._round_money(99.999) == 100.0


def test_resolve_billing_facility_id_single_facility():
    e1 = MagicMock()
    e1.facility_id = 1
    assert billing._resolve_billing_facility_id(e1) == 1


def test_resolve_billing_facility_id_returns_none_when_none():
    e1 = MagicMock()
    e1.facility_id = None
    assert billing._resolve_billing_facility_id(e1) is None


def test_resolve_billing_facility_id_raises_on_mismatch():
    e1 = MagicMock()
    e1.facility_id = 1
    e2 = MagicMock()
    e2.facility_id = 2
    with pytest.raises(HTTPException) as exc:
        billing._resolve_billing_facility_id(e1, e2)
    assert exc.value.status_code == 400


# ══════════════════════════════════════════════════════════════════════
# BILLING — endpoints
# ══════════════════════════════════════════════════════════════════════

def test_billing_services_requires_auth(client):
    assert client.get("/billing/services").status_code == 401


def test_billing_services_requires_billing_or_admin(client):
    h = _auth(client, "bill_patient1")
    assert client.get("/billing/services", headers=h).status_code == 403


def test_billing_create_service_requires_billing_or_admin(client):
    h = _auth(client, "bill_patient2")
    r = client.post("/billing/services", json={
        "service_code": "SVC001", "name": "Test", "service_type": "lab", "unit_price": 100
    }, headers=h)
    assert r.status_code == 403


def test_billing_create_service_success(client, db_session):
    h = _auth(client, "bill_admin1")
    _set_role(db_session, "bill_admin1", "admin")
    r = client.post("/billing/services", json={
        "service_code": "LAB001",
        "name": "Complete Blood Count",
        "service_type": "lab",
        "unit_price": 500.0,
    }, headers=h)
    assert r.status_code == 200
    data = r.json()
    assert data["service_code"] == "LAB001"
    assert data["unit_price"] == 500.0


def test_billing_create_service_rejects_negative_price(client, db_session):
    h = _auth(client, "bill_admin2")
    _set_role(db_session, "bill_admin2", "admin")
    r = client.post("/billing/services", json={
        "service_code": "NEG001", "name": "Bad Service",
        "service_type": "lab", "unit_price": -100.0,
    }, headers=h)
    assert r.status_code == 400


def test_billing_create_service_409_on_duplicate(client, db_session):
    h = _auth(client, "bill_admin3")
    _set_role(db_session, "bill_admin3", "admin")
    payload = {"service_code": "DUP001", "name": "Dup", "service_type": "lab", "unit_price": 100}
    client.post("/billing/services", json=payload, headers=h)
    r = client.post("/billing/services", json=payload, headers=h)
    assert r.status_code == 409


def test_billing_list_services_returns_list(client, db_session):
    h = _auth(client, "bill_admin4")
    _set_role(db_session, "bill_admin4", "admin")
    r = client.get("/billing/services", headers=h)
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_billing_create_invoice_requires_auth(client):
    assert client.post("/billing/invoices", json={}).status_code == 401


def test_billing_create_invoice_requires_billing_or_admin(client):
    h = _auth(client, "bill_patient3")
    r = client.post("/billing/invoices", json={"patient_id": 1, "items": []}, headers=h)
    assert r.status_code == 403


def test_billing_create_invoice_rejects_empty_items(client, db_session):
    h = _auth(client, "bill_admin5")
    _set_role(db_session, "bill_admin5", "admin")
    _auth(client, "bill_pat1")
    pat_id = _get_id(db_session, "bill_pat1")
    r = client.post("/billing/invoices", json={
        "patient_id": pat_id, "items": []
    }, headers=h)
    assert r.status_code == 400
    assert "item" in r.json()["detail"].lower()


def test_billing_create_invoice_success(client, db_session):
    h = _auth(client, "bill_admin6")
    _set_role(db_session, "bill_admin6", "admin")
    _auth(client, "bill_pat2")
    pat_id = _get_id(db_session, "bill_pat2")

    # Create a service first
    svc = client.post("/billing/services", json={
        "service_code": "INV_SVC001", "name": "Consultation", "service_type": "consultation", "unit_price": 750.0
    }, headers=h).json()

    r = client.post("/billing/invoices", json={
        "patient_id": pat_id,
        "items": [{"service_id": svc["id"], "quantity": 1, "description": "Consultation"}],
        "discount_amount": 0,
        "tax_amount": 0,
    }, headers=h)
    assert r.status_code == 200
    data = r.json()
    assert data["total_amount"] == 750.0
    assert data["status"] == "issued"


def test_billing_patient_invoices_requires_patient_role(client, db_session):
    h = _auth(client, "bill_admin7")
    _set_role(db_session, "bill_admin7", "admin")
    r = client.get("/billing/patient/invoices", headers=h)
    assert r.status_code == 403


def test_billing_patient_invoices_returns_empty(client):
    h = _auth(client, "bill_pat3")
    r = client.get("/billing/patient/invoices", headers=h)
    assert r.status_code == 200
    assert r.json() == []


def test_billing_metrics_requires_billing_or_admin(client):
    h = _auth(client, "bill_patient4")
    assert client.get("/billing/admin/metrics", headers=h).status_code == 403


def test_billing_metrics_returns_counts(client, db_session):
    h = _auth(client, "bill_admin8")
    _set_role(db_session, "bill_admin8", "admin")
    r = client.get("/billing/admin/metrics", headers=h)
    assert r.status_code == 200
    data = r.json()
    assert "total_invoices" in data
    assert "total_collected" in data
    assert "operations_note" in data


def test_billing_record_payment_returns_404_for_unknown_invoice(client, db_session):
    h = _auth(client, "bill_admin9")
    _set_role(db_session, "bill_admin9", "admin")
    r = client.post("/billing/invoices/99999/payments", json={
        "amount": 100.0, "payment_method": "cash"
    }, headers=h)
    assert r.status_code == 404


def test_billing_admin_invoices_returns_list(client, db_session):
    h = _auth(client, "bill_admin10")
    _set_role(db_session, "bill_admin10", "admin")
    r = client.get("/billing/admin/invoices", headers=h)
    assert r.status_code == 200
    assert isinstance(r.json(), list)


# ══════════════════════════════════════════════════════════════════════
# TELEMETRY
# ══════════════════════════════════════════════════════════════════════

def test_generate_telemetry_snapshot_returns_expected_keys():
    snapshot = telemetry._generate_telemetry_snapshot()
    for key in ("timestamp", "active_census", "total_capacity",
                "department_loads", "bed_units", "ed_boarding"):
        assert key in snapshot


def test_generate_telemetry_snapshot_active_census_within_capacity():
    snapshot = telemetry._generate_telemetry_snapshot()
    assert snapshot["active_census"] <= snapshot["total_capacity"]


def test_generate_telemetry_snapshot_department_loads_have_status():
    snapshot = telemetry._generate_telemetry_snapshot()
    for dept in snapshot["department_loads"]:
        assert dept["status"] in ("Critical", "Elevated", "Stable")


def test_generate_telemetry_snapshot_bed_units_math_consistent():
    snapshot = telemetry._generate_telemetry_snapshot()
    for unit in snapshot["bed_units"]:
        assert unit["occupied"] + unit["cleaning"] + unit["available"] == unit["total"]


def test_build_telemetry_snapshot_requires_admin(db_session):
    patient = models.User(
        username="tel_patient", hashed_password="x", role="patient"
    )
    db_session.add(patient)
    db_session.commit()
    with patch("backend.telemetry.auth.is_admin", return_value=False):
        with pytest.raises(HTTPException) as exc:
            telemetry.build_telemetry_snapshot(db_session, patient)
    assert exc.value.status_code == 403


def test_build_telemetry_snapshot_returns_keys(db_session):
    admin = models.User(
        username="tel_admin", hashed_password="x", role="admin"
    )
    db_session.add(admin)
    db_session.commit()
    with patch("backend.telemetry.auth.is_admin", return_value=True):
        snapshot = telemetry.build_telemetry_snapshot(db_session, admin)
    for key in ("timestamp", "active_census", "total_capacity",
                "department_loads", "bed_units", "source"):
        assert key in snapshot
    assert snapshot["source"] == "database"


def test_user_from_access_token_returns_none_for_bad_token(db_session):
    result = telemetry._user_from_access_token(db_session, "not.a.valid.token")
    assert result is None


def test_is_database_session_true_for_session(db_session):
    assert telemetry._is_database_session(db_session) is True


def test_is_database_session_false_for_non_session():
    assert telemetry._is_database_session("not a session") is False
    assert telemetry._is_database_session(42) is False


def test_telemetry_snapshot_endpoint_requires_admin(client):
    h = _auth(client, "tel_patient1")
    r = client.get("/telemetry/snapshot", headers=h)
    assert r.status_code == 403


def test_telemetry_snapshot_endpoint_returns_data(client, db_session):
    h = _auth(client, "tel_admin1")
    _set_role(db_session, "tel_admin1", "admin")
    r = client.get("/telemetry/snapshot", headers=h)
    assert r.status_code == 200
    data = r.json()
    assert "timestamp" in data
    assert "active_census" in data
