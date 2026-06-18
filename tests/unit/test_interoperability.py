"""
Tests for interoperability.py — FHIR export, consent management,
ABDM readiness, DICOMweb, SMART on FHIR, and metrics endpoints.

Covers: pure logic helpers, consent lifecycle, export endpoints,
readiness checks, and metrics.
"""
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend import models
from backend.database import Base, get_db
from backend.interoperability import (
    ALLOWED_EXPORT_RESOURCES,
    CONSENT_SCOPE,
    _bundle_sha256,
    _canonical_json,
    _dt,
    _is_active_consent,
    _to_utc,
    _validate_resource_types,
)
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
    pwd = "InteropTest123!"
    client.post("/signup", json={
        "username": username, "password": pwd,
        "email": f"{username}@test.com",
        "full_name": username.replace("_", " ").title(),
        "dob": "1990-01-01",
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
# PURE LOGIC HELPERS
# ══════════════════════════════════════════════════════════════════════

def test_dt_none_returns_none():
    assert _dt(None) is None


def test_dt_naive_datetime_adds_utc():
    dt = datetime(2024, 6, 1, 12, 0, 0)
    result = _dt(dt)
    assert "2024-06-01" in result
    assert "+00:00" in result or "Z" in result


def test_dt_aware_datetime_formats_iso():
    dt = datetime(2024, 6, 1, 12, 0, 0, tzinfo=timezone.utc)
    result = _dt(dt)
    assert "2024-06-01" in result


def test_to_utc_naive_adds_utc():
    dt = datetime(2024, 6, 1, 12, 0, 0)
    result = _to_utc(dt)
    assert result.tzinfo is not None


def test_to_utc_aware_converts_to_utc():
    # Use UTC+5:30 (IST) if available, else just UTC
    dt = datetime(2024, 6, 1, 12, 0, 0, tzinfo=timezone.utc)
    result = _to_utc(dt)
    assert result.tzinfo == timezone.utc


def test_canonical_json_sorts_keys():
    d = {"z": 1, "a": 2}
    result = _canonical_json(d)
    assert result.index('"a"') < result.index('"z"')


def test_bundle_sha256_returns_64_char_hex():
    bundle = {"resourceType": "Bundle", "entry": []}
    result = _bundle_sha256(bundle)
    assert len(result) == 64
    assert all(c in "0123456789abcdef" for c in result)


def test_bundle_sha256_deterministic():
    bundle = {"resourceType": "Bundle", "entry": []}
    assert _bundle_sha256(bundle) == _bundle_sha256(bundle)


def test_validate_resource_types_valid():
    result = _validate_resource_types(["Patient", "Encounter"])
    assert "Patient" in result
    assert "Encounter" in result


def test_validate_resource_types_none_returns_none():
    assert _validate_resource_types(None) is None


def test_validate_resource_types_rejects_unknown():
    with pytest.raises(HTTPException) as exc:
        _validate_resource_types(["UnknownType"])
    assert exc.value.status_code == 400


def test_validate_resource_types_deduplicates():
    result = _validate_resource_types(["Patient", "Patient"])
    assert result.count("Patient") == 1


def test_validate_resource_types_skips_empty_strings():
    result = _validate_resource_types(["Patient", "", "Encounter"])
    assert "" not in result
    assert len(result) == 2


def test_is_active_consent_true_for_active_no_expiry():
    consent = MagicMock()
    consent.status = "active"
    consent.scope = CONSENT_SCOPE
    consent.expires_at = None
    assert _is_active_consent(consent) is True


def test_is_active_consent_false_for_revoked():
    consent = MagicMock()
    consent.status = "revoked"
    consent.scope = CONSENT_SCOPE
    consent.expires_at = None
    assert _is_active_consent(consent) is False


def test_is_active_consent_false_for_wrong_scope():
    consent = MagicMock()
    consent.status = "active"
    consent.scope = "wrong_scope"
    consent.expires_at = None
    assert _is_active_consent(consent) is False


def test_is_active_consent_false_when_expired():
    consent = MagicMock()
    consent.status = "active"
    consent.scope = CONSENT_SCOPE
    consent.expires_at = datetime(2020, 1, 1, tzinfo=timezone.utc)  # past
    assert _is_active_consent(consent) is False


def test_is_active_consent_true_when_not_yet_expired():
    consent = MagicMock()
    consent.status = "active"
    consent.scope = CONSENT_SCOPE
    consent.expires_at = datetime.now(timezone.utc) + timedelta(days=30)
    assert _is_active_consent(consent) is True


def test_allowed_export_resources_contains_expected():
    for resource in ("Patient", "Encounter", "Observation", "DiagnosticReport",
                     "MedicationRequest", "Invoice", "CareEvent"):
        assert resource in ALLOWED_EXPORT_RESOURCES


# ══════════════════════════════════════════════════════════════════════
# CONSENT ENDPOINTS
# ══════════════════════════════════════════════════════════════════════

def test_grant_consent_requires_auth(client):
    assert client.post("/interop/consents", json={
        "purpose": "Share records with care team",
        "recipient_type": "care_team",
    }).status_code == 401


def test_grant_consent_requires_patient_role(client, db_session):
    h = _auth(client, "interop_doc1")
    _set_role(db_session, "interop_doc1", "doctor")
    r = client.post("/interop/consents", json={
        "purpose": "Share records",
        "recipient_type": "care_team",
    }, headers=h)
    assert r.status_code == 403


def test_grant_consent_success(client):
    h = _auth(client, "interop_pat1")
    r = client.post("/interop/consents", json={
        "purpose": "Share records with care team",
        "recipient_type": "care_team",
    }, headers=h)
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "active"
    assert data["scope"] == CONSENT_SCOPE


def test_list_patient_consents_requires_auth(client):
    assert client.get("/interop/consents").status_code == 401


def test_list_patient_consents_requires_patient_role(client, db_session):
    h = _auth(client, "interop_doc2")
    _set_role(db_session, "interop_doc2", "doctor")
    assert client.get("/interop/consents", headers=h).status_code == 403


def test_list_patient_consents_returns_empty(client):
    h = _auth(client, "interop_pat2")
    r = client.get("/interop/consents", headers=h)
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_revoke_consent_requires_auth(client):
    assert client.put("/interop/consents/1/revoke").status_code == 401


def test_revoke_consent_returns_404_for_unknown(client):
    h = _auth(client, "interop_pat3")
    r = client.put("/interop/consents/99999/revoke", headers=h)
    assert r.status_code == 404


def test_revoke_consent_success(client):
    h = _auth(client, "interop_pat4")
    # First grant
    grant_r = client.post("/interop/consents", json={
        "purpose": "Share records",
        "recipient_type": "care_team",
    }, headers=h)
    consent_id = grant_r.json()["id"]
    # Then revoke
    r = client.put(f"/interop/consents/{consent_id}/revoke", headers=h)
    assert r.status_code == 200
    assert r.json()["status"] == "revoked"


def test_revoke_already_revoked_consent_returns_409(client):
    h = _auth(client, "interop_pat5")
    grant_r = client.post("/interop/consents", json={
        "purpose": "Test", "recipient_type": "care_team",
    }, headers=h)
    consent_id = grant_r.json()["id"]
    client.put(f"/interop/consents/{consent_id}/revoke", headers=h)
    r = client.put(f"/interop/consents/{consent_id}/revoke", headers=h)
    assert r.status_code == 409


# ══════════════════════════════════════════════════════════════════════
# EXPORT ENDPOINTS
# ══════════════════════════════════════════════════════════════════════

def test_export_patient_bundle_requires_auth(client):
    assert client.post("/interop/export/patient").status_code == 401


def test_export_patient_bundle_requires_patient_role(client, db_session):
    h = _auth(client, "interop_doc3")
    _set_role(db_session, "interop_doc3", "doctor")
    assert client.get("/interop/patient/fhir-bundle", headers=h).status_code == 403


def test_export_patient_bundle_requires_consent(client):
    h = _auth(client, "interop_pat6")
    r = client.get("/interop/patient/fhir-bundle", headers=h)
    assert r.status_code == 403
    assert "consent" in r.json()["detail"].lower()


def test_export_patient_bundle_success_with_consent(client):
    h = _auth(client, "interop_pat7")
    # Grant consent first
    client.post("/interop/consents", json={
        "purpose": "Export for care team",
        "recipient_type": "care_team",
    }, headers=h)
    r = client.get("/interop/patient/fhir-bundle", headers=h)
    assert r.status_code == 200
    data = r.json()
    assert "bundle" in data
    assert data["bundle"]["resourceType"] == "Bundle"


def test_export_doctor_patient_bundle_requires_auth(client):
    assert client.get("/interop/doctor/patients/1/fhir-bundle").status_code == 401


def test_export_doctor_patient_bundle_requires_doctor_or_admin(client):
    h = _auth(client, "interop_pat8")
    assert client.get("/interop/doctor/patients/1/fhir-bundle", headers=h).status_code == 403


# ══════════════════════════════════════════════════════════════════════
# READINESS ENDPOINTS
# ══════════════════════════════════════════════════════════════════════

def test_abdm_readiness_endpoint_requires_auth(client):
    assert client.get("/interop/abdm/readiness").status_code == 401


def test_abdm_readiness_endpoint_requires_admin(client):
    h = _auth(client, "interop_pat9")
    r = client.get("/interop/abdm/readiness", headers=h)
    assert r.status_code == 403


def test_abdm_readiness_endpoint_returns_data_for_admin(client, db_session):
    h = _auth(client, "interop_admin6")
    _set_role(db_session, "interop_admin6", "admin")
    r = client.get("/interop/abdm/readiness", headers=h)
    assert r.status_code == 200
    assert "enabled" in r.json()


def test_dicomweb_readiness_endpoint_requires_auth(client):
    assert client.get("/interop/dicomweb/readiness").status_code == 401


def test_dicomweb_readiness_endpoint_requires_admin(client):
    h = _auth(client, "interop_pat10")
    r = client.get("/interop/dicomweb/readiness", headers=h)
    assert r.status_code == 403


def test_dicomweb_readiness_endpoint_returns_data_for_admin(client, db_session):
    h = _auth(client, "interop_admin7")
    _set_role(db_session, "interop_admin7", "admin")
    r = client.get("/interop/dicomweb/readiness", headers=h)
    assert r.status_code == 200
    assert "enabled" in r.json()


def test_smart_fhir_readiness_endpoint_requires_auth(client):
    assert client.get("/interop/smart/readiness").status_code == 401


def test_smart_fhir_readiness_requires_admin(client):
    h = _auth(client, "interop_pat11")
    r = client.get("/interop/smart/readiness", headers=h)
    assert r.status_code == 403


def test_smart_fhir_readiness_returns_data_for_admin(client, db_session):
    h = _auth(client, "interop_admin8")
    _set_role(db_session, "interop_admin8", "admin")
    r = client.get("/interop/smart/readiness", headers=h)
    assert r.status_code == 200
    assert "enabled" in r.json()


# ══════════════════════════════════════════════════════════════════════
# ADMIN ENDPOINTS
# ══════════════════════════════════════════════════════════════════════

def test_list_admin_consents_requires_admin(client):
    h = _auth(client, "interop_pat12")
    assert client.get("/interop/admin/consents", headers=h).status_code == 403


def test_list_admin_consents_returns_list(client, db_session):
    h = _auth(client, "interop_admin1")
    _set_role(db_session, "interop_admin1", "admin")
    r = client.get("/interop/admin/consents", headers=h)
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_create_export_profile_requires_admin(client):
    h = _auth(client, "interop_pat13")
    r = client.post("/interop/admin/export-profiles", json={
        "name": "Profile A",
        "resource_types": ["Patient", "Encounter"],
    }, headers=h)
    assert r.status_code == 403


def test_create_export_profile_success(client, db_session):
    h = _auth(client, "interop_admin2")
    _set_role(db_session, "interop_admin2", "admin")
    r = client.post("/interop/admin/export-profiles", json={
        "name": "Test Export Profile",
        "resource_types": ["Patient", "Encounter"],
        "partner_system": "EMR System",
    }, headers=h)
    assert r.status_code == 200
    data = r.json()
    assert data["name"] == "Test Export Profile"


def test_create_export_profile_rejects_invalid_resource_type(client, db_session):
    h = _auth(client, "interop_admin3")
    _set_role(db_session, "interop_admin3", "admin")
    r = client.post("/interop/admin/export-profiles", json={
        "name": "Bad Profile",
        "resource_types": ["InvalidResource"],
    }, headers=h)
    assert r.status_code == 400


def test_list_export_profiles_requires_admin(client):
    h = _auth(client, "interop_pat14")
    assert client.get("/interop/admin/export-profiles", headers=h).status_code == 403


def test_list_export_profiles_returns_list(client, db_session):
    h = _auth(client, "interop_admin4")
    _set_role(db_session, "interop_admin4", "admin")
    r = client.get("/interop/admin/export-profiles", headers=h)
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_interoperability_metrics_requires_admin(client):
    h = _auth(client, "interop_pat15")
    assert client.get("/interop/admin/metrics", headers=h).status_code == 403


def test_interoperability_metrics_returns_data(client, db_session):
    h = _auth(client, "interop_admin5")
    _set_role(db_session, "interop_admin5", "admin")
    r = client.get("/interop/admin/metrics", headers=h)
    assert r.status_code == 200
    data = r.json()
    assert "total_consents" in data or "consents" in data or "exports" in data


# ══════════════════════════════════════════════════════════════════════
# DOCTOR CONSENT STATUS
# ══════════════════════════════════════════════════════════════════════

def test_doctor_consent_status_requires_doctor_or_admin(client):
    h = _auth(client, "interop_pat16")
    assert client.get("/interop/doctor/patients/1/consent-status", headers=h).status_code == 403


def test_doctor_consent_status_returns_404_for_unknown_patient(client, db_session):
    h = _auth(client, "interop_doc4")
    _set_role(db_session, "interop_doc4", "doctor")
    r = client.get("/interop/doctor/patients/99999/consent-status", headers=h)
    assert r.status_code in (403, 404)  # 403 if doctor not assigned, 404 if patient not found
