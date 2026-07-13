"""
Tests for admin.py, monitoring.py, and operational_health.py.

Covers: admin CRUD (users, roles, facilities, audit logs, stats),
monitoring signal generation logic, vital submission, admin patterns,
and operational health report checks.
"""
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from pydantic import ValidationError
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend import models
from backend.database import Base, get_db
from backend.main import app
from backend.monitoring import _generate_signals, _validate_vital_measurements
from backend.operational_health import (
    _check,
    _duplicate_route_check,
    _overall_status,
    _route_pairs,
    build_operational_health_report,
)
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


def _signup_and_login(client, username, role="patient"):
    pwd = "AdminTest123!"
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


# ═══════════════════════════════════════════════════════════════════════
# ADMIN ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════

def test_admin_stats_requires_admin(client):
    h = _signup_and_login(client, "adm_patient1")
    r = client.get("/admin/stats", headers=h)
    assert r.status_code == 403


def test_admin_stats_returns_counts(client, db_session):
    h = _signup_and_login(client, "adm_admin1")
    _set_role(db_session, "adm_admin1", "admin")
    r = client.get("/admin/stats", headers=h)
    assert r.status_code == 200
    data = r.json()
    assert "total_users" in data
    assert "total_predictions" in data
    assert "server_status" in data
    assert data["server_status"] == "Online"


def test_admin_get_users_requires_admin(client):
    h = _signup_and_login(client, "adm_patient2")
    r = client.get("/admin/users", headers=h)
    assert r.status_code == 403


def test_admin_get_users_returns_list(client, db_session):
    h = _signup_and_login(client, "adm_admin2")
    _set_role(db_session, "adm_admin2", "admin")
    r = client.get("/admin/users", headers=h)
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_admin_get_patients_returns_only_patients(client, db_session):
    h = _signup_and_login(client, "adm_admin3")
    _set_role(db_session, "adm_admin3", "admin")
    _signup_and_login(client, "adm_patient3")  # patient
    _signup_and_login(client, "adm_doc1")
    _set_role(db_session, "adm_doc1", "doctor")

    r = client.get("/admin/patients", headers=h)
    assert r.status_code == 200
    for user in r.json():
        assert user["role"] == "patient"


def test_admin_get_patient_profile_returns_404_for_unknown(client, db_session):
    h = _signup_and_login(client, "adm_admin4")
    _set_role(db_session, "adm_admin4", "admin")
    r = client.get("/admin/patients/99999", headers=h)
    assert r.status_code == 404


def test_admin_get_patient_profile_returns_data(client, db_session):
    h = _signup_and_login(client, "adm_admin5")
    _set_role(db_session, "adm_admin5", "admin")
    _signup_and_login(client, "adm_patient4")
    patient_id = _get_id(db_session, "adm_patient4")

    r = client.get(f"/admin/patients/{patient_id}", headers=h)
    assert r.status_code == 200
    assert r.json()["username"] == "adm_patient4"


def test_admin_update_role_requires_admin(client):
    h = _signup_and_login(client, "adm_patient5")
    r = client.put("/admin/users/1/role?role=doctor", headers=h)
    assert r.status_code == 403


def test_admin_update_role_success(client, db_session):
    h = _signup_and_login(client, "adm_admin6")
    _set_role(db_session, "adm_admin6", "admin")
    _signup_and_login(client, "adm_patient6")
    patient_id = _get_id(db_session, "adm_patient6")

    r = client.put(f"/admin/users/{patient_id}/role?role=doctor", headers=h)
    assert r.status_code == 200
    assert "doctor" in r.json()["message"]


def test_admin_update_role_rejects_invalid_role(client, db_session):
    h = _signup_and_login(client, "adm_admin7")
    _set_role(db_session, "adm_admin7", "admin")
    _signup_and_login(client, "adm_patient7")
    patient_id = _get_id(db_session, "adm_patient7")

    r = client.put(f"/admin/users/{patient_id}/role?role=superuser", headers=h)
    assert r.status_code == 400


def test_admin_update_role_cannot_change_own_admin_role(client, db_session):
    h = _signup_and_login(client, "adm_admin8")
    _set_role(db_session, "adm_admin8", "admin")
    admin_id = _get_id(db_session, "adm_admin8")

    r = client.put(f"/admin/users/{admin_id}/role?role=patient", headers=h)
    assert r.status_code == 400


def test_admin_delete_user_success(client, db_session):
    h = _signup_and_login(client, "adm_admin9")
    _set_role(db_session, "adm_admin9", "admin")
    _signup_and_login(client, "adm_target1")
    target_id = _get_id(db_session, "adm_target1")

    r = client.delete(f"/admin/users/{target_id}", headers=h)
    assert r.status_code == 200
    assert "deleted" in r.json()["message"].lower()


def test_admin_delete_user_cannot_delete_self(client, db_session):
    h = _signup_and_login(client, "adm_admin10")
    _set_role(db_session, "adm_admin10", "admin")
    admin_id = _get_id(db_session, "adm_admin10")

    r = client.delete(f"/admin/users/{admin_id}", headers=h)
    assert r.status_code == 400


def test_admin_delete_user_returns_404_for_unknown(client, db_session):
    h = _signup_and_login(client, "adm_admin11")
    _set_role(db_session, "adm_admin11", "admin")
    r = client.delete("/admin/users/99999", headers=h)
    assert r.status_code == 404


def test_admin_audit_logs_requires_admin(client):
    h = _signup_and_login(client, "adm_patient8")
    r = client.get("/admin/audit-logs", headers=h)
    assert r.status_code == 403


def test_admin_audit_logs_returns_list(client, db_session):
    h = _signup_and_login(client, "adm_admin12")
    _set_role(db_session, "adm_admin12", "admin")
    r = client.get("/admin/audit-logs", headers=h)
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_admin_ai_functions_requires_admin(client):
    h = _signup_and_login(client, "adm_patient9")
    r = client.get("/admin/ai-functions", headers=h)
    assert r.status_code == 403


def test_admin_ai_functions_returns_registry(client, db_session):
    h = _signup_and_login(client, "adm_admin13")
    _set_role(db_session, "adm_admin13", "admin")
    r = client.get("/admin/ai-functions", headers=h)
    assert r.status_code == 200
    data = r.json()
    assert "functions" in data
    assert len(data["functions"]) > 0


def test_admin_incident_readiness_requires_admin(client):
    h = _signup_and_login(client, "adm_patient10")
    r = client.get("/admin/incident-readiness", headers=h)
    assert r.status_code == 403


def test_admin_incident_readiness_returns_report(client, db_session):
    h = _signup_and_login(client, "adm_admin14")
    _set_role(db_session, "adm_admin14", "admin")
    r = client.get("/admin/incident-readiness", headers=h)
    assert r.status_code == 200
    assert "status" in r.json()


def test_admin_retention_readiness_requires_admin(client):
    h = _signup_and_login(client, "adm_patient11")
    r = client.get("/admin/retention-readiness", headers=h)
    assert r.status_code == 403


def test_admin_security_assurance_returns_report(client, db_session):
    h = _signup_and_login(client, "adm_admin15")
    _set_role(db_session, "adm_admin15", "admin")
    r = client.get("/admin/security-assurance", headers=h)
    assert r.status_code == 200
    assert "controls" in r.json()


def test_admin_analytics_report_returns_defaults_when_no_file(client, db_session):
    h = _signup_and_login(client, "adm_admin16")
    _set_role(db_session, "adm_admin16", "admin")
    r = client.get("/admin/analytics/report", headers=h)
    assert r.status_code == 200
    data = r.json()
    assert "prevalence_rates" in data


def test_admin_assign_facility_returns_404_for_unknown_facility(client, db_session):
    h = _signup_and_login(client, "adm_admin17")
    _set_role(db_session, "adm_admin17", "admin")
    _signup_and_login(client, "adm_patient12")
    patient_id = _get_id(db_session, "adm_patient12")

    r = client.put(f"/admin/users/{patient_id}/facility?facility_id=99999", headers=h)
    assert r.status_code == 404


# ═══════════════════════════════════════════════════════════════════════
# MONITORING — signal generation (pure logic)
# ═══════════════════════════════════════════════════════════════════════

def _make_vital(**kwargs):
    """Create a minimal VitalObservation-like object for signal generation."""
    v = MagicMock()
    v.id = 1
    v.patient_id = 1
    v.facility_id = None
    v.encounter_id = None
    v.department_id = None
    for k, val in kwargs.items():
        setattr(v, k, val)
    # Set unmapped fields to None
    for field in ("heart_rate", "systolic_bp", "diastolic_bp",
                  "spo2", "temperature_c", "respiratory_rate"):
        if not hasattr(v, field) or getattr(v, field) is MagicMock:
            setattr(v, field, kwargs.get(field, None))
    return v


def _make_db_session():
    db = MagicMock()
    db.add = MagicMock()
    return db


def test_generate_signals_spo2_critical_below_90():
    vital = _make_vital(spo2=88.0, systolic_bp=None, diastolic_bp=None,
                        heart_rate=None, temperature_c=None, respiratory_rate=None)
    db = _make_db_session()
    signals = _generate_signals(db, vital)
    assert any(s.severity == "critical" for s in signals)
    assert any(s.signal_type == "oxygen_saturation" for s in signals)


def test_generate_signals_spo2_warning_between_90_and_94():
    vital = _make_vital(spo2=92.0, systolic_bp=None, diastolic_bp=None,
                        heart_rate=None, temperature_c=None, respiratory_rate=None)
    db = _make_db_session()
    signals = _generate_signals(db, vital)
    spo2_signals = [s for s in signals if s.signal_type == "oxygen_saturation"]
    assert len(spo2_signals) == 1
    assert spo2_signals[0].severity == "warning"


def test_generate_signals_no_signal_for_normal_spo2():
    vital = _make_vital(spo2=98.0, systolic_bp=None, diastolic_bp=None,
                        heart_rate=None, temperature_c=None, respiratory_rate=None)
    db = _make_db_session()
    signals = _generate_signals(db, vital)
    assert not any(s.signal_type == "oxygen_saturation" for s in signals)


def test_generate_signals_bp_critical_above_180():
    vital = _make_vital(spo2=None, systolic_bp=185.0, diastolic_bp=95.0,
                        heart_rate=None, temperature_c=None, respiratory_rate=None)
    db = _make_db_session()
    signals = _generate_signals(db, vital)
    bp_signals = [s for s in signals if s.signal_type == "blood_pressure"]
    assert len(bp_signals) == 1
    assert bp_signals[0].severity == "critical"


def test_generate_signals_bp_warning_stage2():
    vital = _make_vital(spo2=None, systolic_bp=145.0, diastolic_bp=92.0,
                        heart_rate=None, temperature_c=None, respiratory_rate=None)
    db = _make_db_session()
    signals = _generate_signals(db, vital)
    bp_signals = [s for s in signals if s.signal_type == "blood_pressure"]
    assert len(bp_signals) == 1
    assert bp_signals[0].severity == "warning"


def test_generate_signals_no_bp_signal_for_normal():
    vital = _make_vital(spo2=None, systolic_bp=120.0, diastolic_bp=80.0,
                        heart_rate=None, temperature_c=None, respiratory_rate=None)
    db = _make_db_session()
    signals = _generate_signals(db, vital)
    assert not any(s.signal_type == "blood_pressure" for s in signals)


def test_generate_signals_heart_rate_critical_below_40():
    vital = _make_vital(spo2=None, systolic_bp=None, diastolic_bp=None,
                        heart_rate=35.0, temperature_c=None, respiratory_rate=None)
    db = _make_db_session()
    signals = _generate_signals(db, vital)
    hr_signals = [s for s in signals if s.signal_type == "heart_rate"]
    assert hr_signals[0].severity == "critical"


def test_generate_signals_heart_rate_warning_between_50_and_120():
    vital = _make_vital(spo2=None, systolic_bp=None, diastolic_bp=None,
                        heart_rate=45.0, temperature_c=None, respiratory_rate=None)
    db = _make_db_session()
    signals = _generate_signals(db, vital)
    hr_signals = [s for s in signals if s.signal_type == "heart_rate"]
    assert hr_signals[0].severity == "warning"


def test_generate_signals_temperature_critical_below_35():
    vital = _make_vital(spo2=None, systolic_bp=None, diastolic_bp=None,
                        heart_rate=None, temperature_c=34.5, respiratory_rate=None)
    db = _make_db_session()
    signals = _generate_signals(db, vital)
    temp_signals = [s for s in signals if s.signal_type == "temperature"]
    assert temp_signals[0].severity == "critical"


def test_generate_signals_temperature_warning_fever():
    vital = _make_vital(spo2=None, systolic_bp=None, diastolic_bp=None,
                        heart_rate=None, temperature_c=38.5, respiratory_rate=None)
    db = _make_db_session()
    signals = _generate_signals(db, vital)
    temp_signals = [s for s in signals if s.signal_type == "temperature"]
    assert temp_signals[0].severity == "warning"


def test_generate_signals_respiratory_rate_warning():
    vital = _make_vital(spo2=None, systolic_bp=None, diastolic_bp=None,
                        heart_rate=None, temperature_c=None, respiratory_rate=8.0)
    db = _make_db_session()
    signals = _generate_signals(db, vital)
    rr_signals = [s for s in signals if s.signal_type == "respiratory_rate"]
    assert len(rr_signals) == 1


def test_generate_signals_no_signals_for_normal_vitals():
    vital = _make_vital(spo2=98.0, systolic_bp=120.0, diastolic_bp=80.0,
                        heart_rate=70.0, temperature_c=37.0, respiratory_rate=16.0)
    db = _make_db_session()
    signals = _generate_signals(db, vital)
    assert len(signals) == 0


def test_generate_signals_multiple_abnormal_vitals():
    vital = _make_vital(spo2=88.0, systolic_bp=185.0, diastolic_bp=120.0,
                        heart_rate=35.0, temperature_c=34.0, respiratory_rate=None)
    db = _make_db_session()
    signals = _generate_signals(db, vital)
    assert len(signals) >= 3


# ── _validate_vital_measurements ─────────────────────────────────────────────

def test_validate_vital_measurements_raises_when_all_none():
    from backend import schemas
    vital = schemas.VitalObservationCreate(
        patient_id=1,
        heart_rate=None, systolic_bp=None, diastolic_bp=None,
        spo2=None, temperature_c=None, respiratory_rate=None,
    )
    with pytest.raises(HTTPException) as exc:
        _validate_vital_measurements(vital)
    assert exc.value.status_code == 400


def test_validate_vital_measurements_raises_for_out_of_range():
    from backend import schemas

    with pytest.raises(ValidationError, match="Heart rate must be between 20 and 250 bpm"):
        schemas.VitalObservationCreate(
            patient_id=1,
            heart_rate=300.0,
        )


def test_validate_vital_measurements_passes_for_valid():
    from backend import schemas
    vital = schemas.VitalObservationCreate(
        patient_id=1,
        heart_rate=75.0,
        spo2=98.0,
    )
    _validate_vital_measurements(vital)  # Should not raise


# ── Monitoring endpoints ──────────────────────────────────────────────────────

def test_get_patient_vitals_requires_auth(client):
    r = client.get("/monitoring/patient/vitals")
    assert r.status_code == 401


def test_get_patient_vitals_requires_patient_role(client, db_session):
    h = _signup_and_login(client, "mon_doc1")
    _set_role(db_session, "mon_doc1", "doctor")
    r = client.get("/monitoring/patient/vitals", headers=h)
    assert r.status_code == 403


def test_get_patient_vitals_returns_empty_list(client):
    h = _signup_and_login(client, "mon_patient1")
    r = client.get("/monitoring/patient/vitals", headers=h)
    assert r.status_code == 200
    assert r.json() == []


def test_submit_vitals_requires_auth(client):
    r = client.post("/monitoring/vitals", json={"patient_id": 1, "heart_rate": 75})
    assert r.status_code == 401


def test_submit_vitals_patient_submits_own(client, db_session):
    h = _signup_and_login(client, "mon_patient2")
    patient_id = _get_id(db_session, "mon_patient2")

    r = client.post("/monitoring/vitals", json={
        "patient_id": patient_id,
        "heart_rate": 75.0,
        "spo2": 98.0,
    }, headers=h)
    assert r.status_code == 200
    data = r.json()
    assert "vital" in data
    assert "signals" in data


def test_submit_vitals_generates_signal_for_low_spo2(client, db_session):
    h = _signup_and_login(client, "mon_patient3")
    patient_id = _get_id(db_session, "mon_patient3")

    r = client.post("/monitoring/vitals", json={
        "patient_id": patient_id,
        "spo2": 88.0,
    }, headers=h)
    assert r.status_code == 200
    data = r.json()
    assert len(data["signals"]) > 0
    signal_types = [s["signal_type"] for s in data["signals"]]
    assert "oxygen_saturation" in signal_types


def test_admin_monitoring_patterns_requires_admin(client):
    h = _signup_and_login(client, "mon_patient4")
    r = client.get("/monitoring/admin/patterns", headers=h)
    assert r.status_code == 403


def test_admin_monitoring_patterns_returns_counts(client, db_session):
    h = _signup_and_login(client, "mon_admin1")
    _set_role(db_session, "mon_admin1", "admin")
    r = client.get("/monitoring/admin/patterns", headers=h)
    assert r.status_code == 200
    data = r.json()
    assert "total_vital_observations" in data
    assert "open_signals" in data
    assert "clinical_safety_note" in data


def test_doctor_patterns_requires_doctor_or_admin(client):
    h = _signup_and_login(client, "mon_patient5")
    r = client.get("/monitoring/doctor/patterns", headers=h)
    assert r.status_code == 403


def test_doctor_patterns_returns_data_for_doctor(client, db_session):
    h = _signup_and_login(client, "mon_doc2")
    _set_role(db_session, "mon_doc2", "doctor")
    r = client.get("/monitoring/doctor/patterns", headers=h)
    assert r.status_code == 200
    data = r.json()
    assert "assigned_patient_count" in data


# ═══════════════════════════════════════════════════════════════════════
# OPERATIONAL HEALTH
# ═══════════════════════════════════════════════════════════════════════

def test_overall_status_healthy_when_all_passed():
    checks = [
        {"status": "passed"}, {"status": "passed"},
    ]
    assert _overall_status(checks) == "healthy"


def test_overall_status_degraded_when_warning():
    checks = [
        {"status": "passed"}, {"status": "warning"},
    ]
    assert _overall_status(checks) == "degraded"


def test_overall_status_unhealthy_when_failed():
    checks = [
        {"status": "passed"}, {"status": "failed"},
    ]
    assert _overall_status(checks) == "unhealthy"


def test_check_helper_builds_correct_dict():
    result = _check(
        check_id="test_check",
        name="Test Check",
        status="passed",
        total_count=5,
        failed_count=0,
        detail="all good",
    )
    assert result["id"] == "test_check"
    assert result["status"] == "passed"
    assert result["total_count"] == 5
    assert result["failed_count"] == 0


def test_route_pairs_extracts_from_api_routes():
    from fastapi.routing import APIRoute
    mock_route = MagicMock(spec=APIRoute)
    mock_route.methods = {"GET", "POST"}
    mock_route.path = "/test/path"
    pairs = _route_pairs([mock_route])
    assert ("GET", "/test/path") in pairs or ("POST", "/test/path") in pairs


def test_route_pairs_handles_tuple_format():
    pairs = _route_pairs([("GET", "/api/test"), ("POST", "/api/other")])
    assert ("GET", "/api/test") in pairs
    assert ("POST", "/api/other") in pairs


def test_duplicate_route_check_passes_for_unique_routes():
    routes = [("GET", "/a"), ("POST", "/a"), ("GET", "/b")]
    result = _duplicate_route_check(routes)
    assert result["status"] == "passed"
    assert result["failed_count"] == 0


def test_duplicate_route_check_fails_for_duplicates():
    routes = [("GET", "/a"), ("GET", "/a"), ("POST", "/b")]
    result = _duplicate_route_check(routes)
    assert result["status"] == "failed"
    assert result["failed_count"] == 1


def test_build_operational_health_report_returns_all_keys(db_session):
    result = build_operational_health_report(
        db_session,
        routes=[("GET", "/health"), ("POST", "/data")],
        facility_id=None,
    )
    assert "status" in result
    assert "checks" in result
    assert "security_headers" in result
    assert "privacy_note" in result
    assert result["source"] == "backend.operational_health"


def test_build_operational_health_report_has_db_check(db_session):
    result = build_operational_health_report(
        db_session, routes=[], facility_id=None
    )
    check_ids = {c["id"] for c in result["checks"]}
    assert "database_reachable" in check_ids


def test_build_operational_health_report_has_ai_registry_check(db_session):
    result = build_operational_health_report(
        db_session, routes=[], facility_id=None
    )
    check_ids = {c["id"] for c in result["checks"]}
    assert "ai_function_registry_valid" in check_ids


def test_admin_operational_health_endpoint(client, db_session):
    h = _signup_and_login(client, "ops_admin1")
    _set_role(db_session, "ops_admin1", "admin")
    r = client.get("/admin/operational-health", headers=h)
    assert r.status_code == 200
    data = r.json()
    assert "status" in data
    assert "checks" in data
    assert data["status"] in ("healthy", "degraded", "unhealthy")
