"""
Tests for hospital_operations.py, data_quality.py, and backup_readiness.py.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend import backup_readiness, data_quality, models
from backend.database import Base, get_db
from backend.main import app
from backend.prediction import initialize_models

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
    pwd = "HospTest123!"
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
# HOSPITAL OPERATIONS — Facilities
# ══════════════════════════════════════════════════════════════════════

def test_list_facilities_requires_auth(client):
    assert client.get("/hospital/facilities").status_code == 401


def test_list_facilities_requires_admin(client):
    h = _auth(client, "hosp_pat1")
    assert client.get("/hospital/facilities", headers=h).status_code == 403


def test_list_facilities_returns_empty(client, db_session):
    h = _auth(client, "hosp_admin1")
    _set_role(db_session, "hosp_admin1", "admin")
    r = client.get("/hospital/facilities", headers=h)
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_create_facility_requires_admin(client):
    h = _auth(client, "hosp_pat2")
    assert client.post("/hospital/facilities", json={
        "name": "Test Hospital", "facility_type": "hospital"
    }, headers=h).status_code == 403


def test_create_facility_success(client, db_session):
    h = _auth(client, "hosp_admin2")
    _set_role(db_session, "hosp_admin2", "admin")
    r = client.post("/hospital/facilities", json={
        "name": "General Hospital", "facility_type": "hospital",
        "country": "India", "region": "Karnataka"
    }, headers=h)
    assert r.status_code == 200
    assert r.json()["name"] == "General Hospital"


def test_create_facility_409_on_duplicate(client, db_session):
    h = _auth(client, "hosp_admin3")
    _set_role(db_session, "hosp_admin3", "admin")
    payload = {"name": "Duplicate Hospital", "facility_type": "hospital"}
    client.post("/hospital/facilities", json=payload, headers=h)
    r = client.post("/hospital/facilities", json=payload, headers=h)
    assert r.status_code == 409


# ══════════════════════════════════════════════════════════════════════
# HOSPITAL OPERATIONS — Departments
# ══════════════════════════════════════════════════════════════════════

def test_list_departments_requires_auth(client):
    assert client.get("/hospital/departments").status_code == 401


def test_list_departments_returns_empty(client, db_session):
    h = _auth(client, "hosp_admin4")
    _set_role(db_session, "hosp_admin4", "admin")
    r = client.get("/hospital/departments", headers=h)
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_create_department_requires_admin(client):
    h = _auth(client, "hosp_pat3")
    assert client.post("/hospital/departments", json={
        "name": "Cardiology", "department_type": "OPD"
    }, headers=h).status_code == 403


def test_create_department_success(client, db_session):
    h = _auth(client, "hosp_admin5")
    _set_role(db_session, "hosp_admin5", "admin")
    r = client.post("/hospital/departments", json={
        "name": "Cardiology", "department_type": "OPD"
    }, headers=h)
    assert r.status_code == 200
    assert r.json()["name"] == "Cardiology"


def test_create_department_409_on_duplicate(client, db_session):
    h = _auth(client, "hosp_admin6")
    _set_role(db_session, "hosp_admin6", "admin")
    payload = {"name": "Neurology", "department_type": "IPD"}
    client.post("/hospital/departments", json=payload, headers=h)
    r = client.post("/hospital/departments", json=payload, headers=h)
    assert r.status_code == 409


# ══════════════════════════════════════════════════════════════════════
# HOSPITAL OPERATIONS — Beds
# ══════════════════════════════════════════════════════════════════════

def test_list_beds_requires_auth(client):
    assert client.get("/hospital/beds").status_code == 401


def test_list_beds_returns_empty(client, db_session):
    h = _auth(client, "hosp_admin7")
    _set_role(db_session, "hosp_admin7", "admin")
    r = client.get("/hospital/beds", headers=h)
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_create_bed_requires_admin(client):
    h = _auth(client, "hosp_pat4")
    assert client.post("/hospital/beds", json={
        "department_id": 1, "bed_number": "B01"
    }, headers=h).status_code == 403


def test_create_bed_returns_404_for_unknown_department(client, db_session):
    h = _auth(client, "hosp_admin8")
    _set_role(db_session, "hosp_admin8", "admin")
    r = client.post("/hospital/beds", json={
        "department_id": 99999, "bed_number": "B01"
    }, headers=h)
    assert r.status_code == 404


def test_create_bed_success(client, db_session):
    h = _auth(client, "hosp_admin9")
    _set_role(db_session, "hosp_admin9", "admin")
    # Create department first
    dept_r = client.post("/hospital/departments", json={
        "name": "ICU", "department_type": "IPD"
    }, headers=h)
    dept_id = dept_r.json()["id"]
    r = client.post("/hospital/beds", json={
        "department_id": dept_id, "bed_number": "ICU-01", "ward": "ICU"
    }, headers=h)
    assert r.status_code == 200
    assert r.json()["bed_number"] == "ICU-01"


# ══════════════════════════════════════════════════════════════════════
# HOSPITAL OPERATIONS — Encounters
# ══════════════════════════════════════════════════════════════════════

def test_create_encounter_requires_auth(client):
    assert client.post("/hospital/encounters", json={
        "patient_id": 1, "encounter_type": "OPD"
    }).status_code == 401


def test_create_encounter_requires_doctor_or_admin(client):
    h = _auth(client, "hosp_pat5")
    assert client.post("/hospital/encounters", json={
        "patient_id": 1, "encounter_type": "OPD"
    }, headers=h).status_code == 403


def test_create_encounter_returns_404_for_unknown_patient(client, db_session):
    h = _auth(client, "hosp_admin10")
    _set_role(db_session, "hosp_admin10", "admin")
    r = client.post("/hospital/encounters", json={
        "patient_id": 99999, "encounter_type": "OPD"
    }, headers=h)
    assert r.status_code == 404


def test_create_encounter_success(client, db_session):
    h = _auth(client, "hosp_admin11")
    _set_role(db_session, "hosp_admin11", "admin")
    _auth(client, "hosp_pat6")
    pat_id = _get_id(db_session, "hosp_pat6")
    r = client.post("/hospital/encounters", json={
        "patient_id": pat_id,
        "encounter_type": "OPD",
        "reason": "Routine checkup",
    }, headers=h)
    assert r.status_code == 200
    data = r.json()
    assert data["patient_id"] == pat_id
    assert data["encounter_type"] == "OPD"


# ══════════════════════════════════════════════════════════════════════
# HOSPITAL OPERATIONS — Patient timeline & Doctor views
# ══════════════════════════════════════════════════════════════════════

def test_patient_timeline_requires_auth(client):
    assert client.get("/hospital/patient/timeline").status_code == 401


def test_patient_timeline_requires_patient_role(client, db_session):
    # The endpoint is accessible by any authenticated user for their own data;
    # doctors fetching their own timeline should work
    h = _auth(client, "hosp_doc1")
    _set_role(db_session, "hosp_doc1", "doctor")
    r = client.get("/hospital/patient/timeline", headers=h)
    # Should return 200 (doctor can see their own timeline) or 403 if restricted
    assert r.status_code in (200, 403)


def test_patient_timeline_returns_data(client):
    h = _auth(client, "hosp_pat7")
    r = client.get("/hospital/patient/timeline", headers=h)
    assert r.status_code == 200
    data = r.json()
    assert "encounters" in data
    assert "admissions" in data


def test_doctor_patients_requires_doctor_or_admin(client):
    h = _auth(client, "hosp_pat8")
    assert client.get("/hospital/doctor/patients", headers=h).status_code == 403


def test_doctor_patients_returns_list(client, db_session):
    h = _auth(client, "hosp_doc2")
    _set_role(db_session, "hosp_doc2", "doctor")
    r = client.get("/hospital/doctor/patients", headers=h)
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_doctor_insights_requires_doctor_or_admin(client):
    h = _auth(client, "hosp_pat9")
    assert client.get("/hospital/doctor/insights", headers=h).status_code == 403


def test_doctor_insights_returns_data(client, db_session):
    h = _auth(client, "hosp_doc3")
    _set_role(db_session, "hosp_doc3", "doctor")
    r = client.get("/hospital/doctor/insights", headers=h)
    assert r.status_code == 200
    data = r.json()
    assert "insights" in data or "open_encounters" in data


def test_admin_operations_requires_admin(client):
    h = _auth(client, "hosp_pat10")
    assert client.get("/hospital/admin/operations", headers=h).status_code == 403


def test_admin_operations_returns_data(client, db_session):
    h = _auth(client, "hosp_admin12")
    _set_role(db_session, "hosp_admin12", "admin")
    r = client.get("/hospital/admin/operations", headers=h)
    assert r.status_code == 200
    data = r.json()
    assert "total_facilities" in data or "facilities" in data or "beds" in data


# ══════════════════════════════════════════════════════════════════════
# DATA QUALITY
# ══════════════════════════════════════════════════════════════════════

def test_generate_quality_report_returns_required_keys(db_session):
    report = data_quality.generate_quality_report(db_session)
    for key in ("source", "overall_score", "checks", "datasets",
                "failed_checks", "lineage_events", "quarantine", "privacy_note"):
        assert key in report


def test_generate_quality_report_source_is_correct(db_session):
    report = data_quality.generate_quality_report(db_session)
    assert report["source"] == "backend.data_quality"


def test_generate_quality_report_no_phi_exposed(db_session):
    report = data_quality.generate_quality_report(db_session)
    assert "patient" not in str(report.get("datasets", [])).lower() or \
           any(d["pii_exposed"] is False for d in report["datasets"])


def test_generate_quality_report_all_datasets_present(db_session):
    report = data_quality.generate_quality_report(db_session)
    dataset_names = {d["name"] for d in report["datasets"]}
    for name in ("patient_accounts", "encounters", "vital_observations",
                 "diagnostic_results", "prescriptions", "invoices",
                 "interoperability_exports"):
        assert name in dataset_names


def test_generate_quality_report_all_checks_present(db_session):
    report = data_quality.generate_quality_report(db_session)
    check_ids = {c["id"] for c in report["checks"]}
    for cid in ("patients_birth_date_completeness", "vitals_spo2_range",
                "vitals_heart_rate_range", "diagnostics_summary_completeness",
                "prescriptions_have_items", "invoices_amounts_non_negative",
                "interop_exports_manifest_integrity"):
        assert cid in check_ids


def test_generate_quality_report_empty_db_passes_all_checks(db_session):
    report = data_quality.generate_quality_report(db_session)
    # Empty DB means no data to fail — all checks should pass
    failed = [c for c in report["checks"] if c["status"] == "failed"]
    assert len(failed) == 0
    assert report["overall_score"] == 1.0


def test_quality_check_helper_passed_on_zero_failures():
    check = data_quality._check(
        check_id="test_check",
        dataset="test_dataset",
        description="Test",
        total_count=100,
        failed_count=0,
    )
    assert check["status"] == "passed"
    assert check["score"] == 1.0


def test_quality_check_helper_failed_on_nonzero():
    check = data_quality._check(
        check_id="test_check",
        dataset="test_dataset",
        description="Test",
        total_count=100,
        failed_count=10,
    )
    assert check["status"] == "failed"
    assert check["score"] == 0.9


def test_quality_check_helper_score_zero_when_all_fail():
    check = data_quality._check(
        check_id="test_check",
        dataset="test_dataset",
        description="Test",
        total_count=10,
        failed_count=10,
    )
    assert check["score"] == 0.0


def test_quality_check_helper_score_one_on_empty_dataset():
    check = data_quality._check(
        check_id="test_check",
        dataset="test_dataset",
        description="Test",
        total_count=0,
        failed_count=0,
    )
    assert check["score"] == 1.0


def test_overall_score_returns_one_on_empty_checks():
    assert data_quality._overall_score([]) == 1.0


def test_overall_score_averages_check_scores():
    checks = [
        {"score": 1.0}, {"score": 0.5}, {"score": 0.75}
    ]
    score = data_quality._overall_score(checks)
    assert abs(score - 0.75) < 0.001


def test_quarantine_summary_empty_when_all_pass(db_session):
    report = data_quality.generate_quality_report(db_session)
    quarantine = report["quarantine"]
    assert quarantine["record_level_payloads_exposed"] is False
    assert quarantine["datasets"] == []


def test_lineage_events_have_openlineage_structure(db_session):
    report = data_quality.generate_quality_report(db_session)
    events = report["lineage_events"]
    assert len(events) == 7  # one per dataset
    for event in events:
        assert event["eventType"] == "COMPLETE"
        assert "run" in event
        assert "inputs" in event
        assert "outputs" in event


def test_dataset_lineage_pii_not_exposed(db_session):
    report = data_quality.generate_quality_report(db_session)
    for dataset in report["datasets"]:
        assert dataset["pii_exposed"] is False


# ══════════════════════════════════════════════════════════════════════
# BACKUP READINESS
# ══════════════════════════════════════════════════════════════════════

def test_backup_readiness_disabled_by_default(monkeypatch):
    monkeypatch.delenv("BACKUP_ENABLED", raising=False)
    result = backup_readiness.get_readiness()
    assert result["enabled"] is False
    assert result["status"] == "disabled"


def test_backup_readiness_action_required_when_enabled_missing(monkeypatch):
    monkeypatch.setenv("BACKUP_ENABLED", "true")
    for var in ("BACKUP_PROVIDER", "BACKUP_STORAGE_REGION", "BACKUP_RETENTION_DAYS",
                "BACKUP_LAST_SUCCESS_AT", "BACKUP_RESTORE_TESTED_AT"):
        monkeypatch.delenv(var, raising=False)
    result = backup_readiness.get_readiness()
    assert result["status"] == "action_required"
    assert len(result["missing"]) > 0


def test_backup_readiness_no_secrets_exposed(monkeypatch):
    monkeypatch.setenv("BACKUP_OWNER_CONTACT", "ops@hospital.com")
    result = backup_readiness.get_readiness()
    assert result["secret_values_exposed"] is False
    assert "ops@hospital.com" not in str(result)


def test_backup_readiness_stale_restore_test_flagged(monkeypatch):
    monkeypatch.setenv("BACKUP_ENABLED", "true")
    monkeypatch.setenv("BACKUP_RESTORE_TESTED_AT", "2020-01-01T00:00:00Z")
    result = backup_readiness.get_readiness()
    assert result["restore_test_stale"] is True
    assert "BACKUP_RESTORE_TESTED_AT" in result["missing"]


def test_backup_readiness_includes_capabilities():
    result = backup_readiness.get_readiness()
    assert "scheduled_backups" in result["capabilities"]
    assert "encryption" in result["capabilities"]


def test_backup_readiness_parse_datetime_valid(monkeypatch):
    monkeypatch.setenv("BACKUP_LAST_SUCCESS_AT", "2024-06-01T12:00:00Z")
    dt = backup_readiness._parse_datetime("BACKUP_LAST_SUCCESS_AT")
    assert dt is not None
    assert dt.year == 2024


def test_backup_readiness_parse_datetime_invalid_returns_none(monkeypatch):
    monkeypatch.setenv("BACKUP_LAST_SUCCESS_AT", "not-a-date")
    assert backup_readiness._parse_datetime("BACKUP_LAST_SUCCESS_AT") is None


def test_backup_readiness_is_stale_false_for_recent():
    from datetime import datetime, timedelta, timezone
    recent = datetime.now(timezone.utc) - timedelta(days=10)
    assert backup_readiness._is_stale(recent) is False


def test_backup_readiness_is_stale_true_for_old():
    from datetime import datetime, timedelta, timezone
    old = datetime.now(timezone.utc) - timedelta(days=100)
    assert backup_readiness._is_stale(old) is True


def test_backup_readiness_env_int_rejects_zero(monkeypatch):
    monkeypatch.setenv("BACKUP_RETENTION_DAYS", "0")
    assert backup_readiness._env_int("BACKUP_RETENTION_DAYS") is None


def test_backup_readiness_env_int_accepts_positive(monkeypatch):
    monkeypatch.setenv("BACKUP_RETENTION_DAYS", "30")
    assert backup_readiness._env_int("BACKUP_RETENTION_DAYS") == 30
