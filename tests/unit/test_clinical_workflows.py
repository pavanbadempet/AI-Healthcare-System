"""
Tests for diagnostics.py, discharge.py, nursing.py, and pharmacy.py.

All follow the same pattern: role-gated endpoints with facility scoping.
Tests focus on auth enforcement, helper logic, and happy paths.
"""
from unittest.mock import patch

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend import diagnostics, models, pharmacy
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
    pwd = "ClinTest123!"
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
# DIAGNOSTICS
# ══════════════════════════════════════════════════════════════════════

# ── Pure logic ────────────────────────────────────────────────────────

def test_ensure_result_type_matches_order_valid():
    order = models.ClinicalOrder(order_type="lab")
    result = diagnostics._ensure_result_type_matches_order(order, "lab")
    assert result == "lab"


def test_ensure_result_type_matches_order_raises_on_mismatch():
    order = models.ClinicalOrder(order_type="lab")
    with pytest.raises(HTTPException) as exc:
        diagnostics._ensure_result_type_matches_order(order, "procedure")
    assert exc.value.status_code == 400


def test_ensure_result_type_radiology_accepts_imaging_alias():
    order = models.ClinicalOrder(order_type="radiology")
    result = diagnostics._ensure_result_type_matches_order(order, "imaging")
    assert result == "imaging"


def test_require_doctor_or_admin_raises_for_patient():
    u = models.User(username="p", hashed_password="x", role="patient")
    with patch("backend.diagnostics.auth.is_admin", return_value=False):
        with pytest.raises(HTTPException) as exc:
            diagnostics._require_doctor_or_admin(u)
    assert exc.value.status_code == 403


# ── Endpoints ─────────────────────────────────────────────────────────

def test_patient_diagnostic_results_requires_auth(client):
    assert client.get("/diagnostics/patient/results").status_code == 401


def test_patient_diagnostic_results_requires_patient_role(client, db_session):
    h = _auth(client, "diag_doc1")
    _set_role(db_session, "diag_doc1", "doctor")
    assert client.get("/diagnostics/patient/results", headers=h).status_code == 403


def test_patient_diagnostic_results_returns_empty(client):
    h = _auth(client, "diag_pat1")
    r = client.get("/diagnostics/patient/results", headers=h)
    assert r.status_code == 200
    assert r.json() == []


def test_diagnostics_metrics_requires_admin(client):
    h = _auth(client, "diag_pat2")
    assert client.get("/diagnostics/admin/metrics", headers=h).status_code == 403


def test_diagnostics_metrics_returns_counts(client, db_session):
    h = _auth(client, "diag_admin1")
    _set_role(db_session, "diag_admin1", "admin")
    r = client.get("/diagnostics/admin/metrics", headers=h)
    assert r.status_code == 200
    data = r.json()
    assert "total_results" in data
    assert "pending_review" in data
    assert "clinical_safety_note" in data


def test_post_diagnostic_result_requires_doctor_or_admin(client):
    h = _auth(client, "diag_pat3")
    r = client.post("/diagnostics/results", json={
        "order_id": 1, "result_type": "lab", "title": "Test", "summary": "Result"
    }, headers=h)
    assert r.status_code == 403


def test_post_diagnostic_result_returns_404_for_unknown_order(client, db_session):
    h = _auth(client, "diag_admin2")
    _set_role(db_session, "diag_admin2", "admin")
    r = client.post("/diagnostics/results", json={
        "order_id": 99999, "result_type": "lab", "title": "Test", "summary": "Summary"
    }, headers=h)
    assert r.status_code == 404


def test_review_diagnostic_result_returns_404_for_unknown(client, db_session):
    h = _auth(client, "diag_admin3")
    _set_role(db_session, "diag_admin3", "admin")
    r = client.put("/diagnostics/results/99999/review", json={
        "review_status": "reviewed", "review_note": "Looks normal"
    }, headers=h)
    assert r.status_code == 404


def test_doctor_patient_results_requires_auth(client):
    assert client.get("/diagnostics/doctor/patients/1/results").status_code == 401


# ══════════════════════════════════════════════════════════════════════
# DISCHARGE
# ══════════════════════════════════════════════════════════════════════

def test_patient_discharge_summaries_requires_auth(client):
    assert client.get("/discharge/patient/summaries").status_code == 401


def test_patient_discharge_summaries_requires_patient_role(client, db_session):
    h = _auth(client, "dis_doc1")
    _set_role(db_session, "dis_doc1", "doctor")
    assert client.get("/discharge/patient/summaries", headers=h).status_code == 403


def test_patient_discharge_summaries_returns_empty(client):
    h = _auth(client, "dis_pat1")
    r = client.get("/discharge/patient/summaries", headers=h)
    assert r.status_code == 200
    assert r.json() == []


def test_discharge_metrics_requires_admin(client):
    h = _auth(client, "dis_pat2")
    assert client.get("/discharge/admin/metrics", headers=h).status_code == 403


def test_discharge_metrics_returns_counts(client, db_session):
    h = _auth(client, "dis_admin1")
    _set_role(db_session, "dis_admin1", "admin")
    r = client.get("/discharge/admin/metrics", headers=h)
    assert r.status_code == 200
    data = r.json()
    assert "total_summaries" in data
    assert "active_admissions" in data
    assert "clinical_safety_note" in data


def test_create_discharge_summary_requires_doctor_or_admin(client):
    h = _auth(client, "dis_pat3")
    r = client.post("/discharge/summaries", json={
        "patient_id": 1, "admission_id": 1,
        "diagnosis_summary": "Test", "hospital_course": "Course"
    }, headers=h)
    assert r.status_code == 403


def test_create_discharge_summary_returns_404_for_unknown_admission(client, db_session):
    h = _auth(client, "dis_admin2")
    _set_role(db_session, "dis_admin2", "admin")
    _auth(client, "dis_pat4")
    pat_id = _get_id(db_session, "dis_pat4")
    r = client.post("/discharge/summaries", json={
        "patient_id": pat_id, "admission_id": 99999,
        "diagnosis_summary": "Test", "hospital_course": "Course"
    }, headers=h)
    assert r.status_code == 404


def test_finalize_discharge_summary_returns_404_for_unknown(client, db_session):
    h = _auth(client, "dis_admin3")
    _set_role(db_session, "dis_admin3", "admin")
    r = client.put("/discharge/summaries/99999/finalize", headers=h)
    assert r.status_code == 404


def test_discharge_resolve_facility_mismatch_raises():
    from backend.discharge import _resolve_discharge_facility_id
    e1 = models.HospitalFacility(id=1)
    e1.facility_id = 1
    e2 = models.HospitalFacility(id=2)
    e2.facility_id = 2
    with pytest.raises(HTTPException) as exc:
        _resolve_discharge_facility_id(e1, e2)
    assert exc.value.status_code == 400


# ══════════════════════════════════════════════════════════════════════
# NURSING
# ══════════════════════════════════════════════════════════════════════

def test_nurse_tasks_requires_auth(client):
    assert client.get("/nursing/nurse/tasks").status_code == 401


def test_nurse_tasks_requires_nurse_or_admin(client):
    h = _auth(client, "nurs_pat1")
    assert client.get("/nursing/nurse/tasks", headers=h).status_code == 403


def test_nurse_tasks_returns_empty_for_admin(client, db_session):
    h = _auth(client, "nurs_admin1")
    _set_role(db_session, "nurs_admin1", "admin")
    r = client.get("/nursing/nurse/tasks", headers=h)
    assert r.status_code == 200
    assert r.json() == []


def test_patient_nursing_tasks_requires_patient_role(client, db_session):
    h = _auth(client, "nurs_doc1")
    _set_role(db_session, "nurs_doc1", "doctor")
    assert client.get("/nursing/patient/tasks", headers=h).status_code == 403


def test_patient_nursing_tasks_returns_empty(client):
    h = _auth(client, "nurs_pat2")
    r = client.get("/nursing/patient/tasks", headers=h)
    assert r.status_code == 200
    assert r.json() == []


def test_nursing_metrics_requires_admin(client):
    h = _auth(client, "nurs_pat3")
    assert client.get("/nursing/admin/metrics", headers=h).status_code == 403


def test_nursing_metrics_returns_counts(client, db_session):
    h = _auth(client, "nurs_admin2")
    _set_role(db_session, "nurs_admin2", "admin")
    r = client.get("/nursing/admin/metrics", headers=h)
    assert r.status_code == 200
    data = r.json()
    assert "total_tasks" in data
    assert "assigned_tasks" in data
    assert "operations_note" in data


def test_create_nursing_task_requires_doctor_or_admin(client):
    h = _auth(client, "nurs_pat4")
    r = client.post("/nursing/tasks", json={
        "patient_id": 1, "task_type": "medication", "title": "Give meds"
    }, headers=h)
    assert r.status_code == 403


def test_create_nursing_task_returns_404_for_unknown_patient(client, db_session):
    h = _auth(client, "nurs_admin3")
    _set_role(db_session, "nurs_admin3", "admin")
    r = client.post("/nursing/tasks", json={
        "patient_id": 99999, "task_type": "medication", "title": "Give meds"
    }, headers=h)
    assert r.status_code == 404


def test_complete_nursing_task_returns_404_for_unknown(client, db_session):
    h = _auth(client, "nurs_admin4")
    _set_role(db_session, "nurs_admin4", "admin")
    r = client.put("/nursing/tasks/99999/complete", json={"completion_note": "Done"}, headers=h)
    assert r.status_code == 404


def test_nursing_resolve_facility_mismatch_raises():
    from backend.nursing import _resolve_nursing_facility_id
    e1 = models.NursingTask()
    e1.facility_id = 1
    e2 = models.NursingTask()
    e2.facility_id = 2
    with pytest.raises(HTTPException) as exc:
        _resolve_nursing_facility_id(e1, e2)
    assert exc.value.status_code == 400


# ══════════════════════════════════════════════════════════════════════
# PHARMACY
# ══════════════════════════════════════════════════════════════════════

def test_pharmacy_inventory_requires_auth(client):
    assert client.get("/pharmacy/inventory").status_code == 401


def test_pharmacy_inventory_requires_staff(client):
    h = _auth(client, "pharm_pat1")
    assert client.get("/pharmacy/inventory", headers=h).status_code == 403


def test_pharmacy_inventory_returns_empty_for_admin(client, db_session):
    h = _auth(client, "pharm_admin1")
    _set_role(db_session, "pharm_admin1", "admin")
    r = client.get("/pharmacy/inventory", headers=h)
    assert r.status_code == 200
    assert r.json() == []


def test_create_inventory_requires_pharmacy_or_admin(client):
    h = _auth(client, "pharm_pat2")
    r = client.post("/pharmacy/inventory", json={
        "medication_name": "Aspirin", "quantity_on_hand": 100, "reorder_level": 10
    }, headers=h)
    assert r.status_code == 403


def test_create_inventory_rejects_negative_quantity(client, db_session):
    h = _auth(client, "pharm_admin2")
    _set_role(db_session, "pharm_admin2", "admin")
    r = client.post("/pharmacy/inventory", json={
        "medication_name": "Aspirin", "quantity_on_hand": -1, "reorder_level": 5
    }, headers=h)
    assert r.status_code == 400


def test_create_inventory_success(client, db_session):
    h = _auth(client, "pharm_admin3")
    _set_role(db_session, "pharm_admin3", "admin")
    r = client.post("/pharmacy/inventory", json={
        "medication_name": "Paracetamol",
        "strength": "500mg",
        "form": "tablet",
        "quantity_on_hand": 200,
        "reorder_level": 50,
    }, headers=h)
    assert r.status_code == 200
    assert r.json()["medication_name"] == "Paracetamol"


def test_patient_prescriptions_requires_patient_role(client, db_session):
    h = _auth(client, "pharm_doc1")
    _set_role(db_session, "pharm_doc1", "doctor")
    assert client.get("/pharmacy/patient/prescriptions", headers=h).status_code == 403


def test_patient_prescriptions_returns_empty(client):
    h = _auth(client, "pharm_pat3")
    r = client.get("/pharmacy/patient/prescriptions", headers=h)
    assert r.status_code == 200
    assert r.json() == []


def test_create_prescription_requires_doctor_or_admin(client):
    h = _auth(client, "pharm_pat4")
    r = client.post("/pharmacy/prescriptions", json={
        "patient_id": 1, "items": []
    }, headers=h)
    assert r.status_code == 403


def test_create_prescription_rejects_empty_items(client, db_session):
    h = _auth(client, "pharm_admin4")
    _set_role(db_session, "pharm_admin4", "admin")
    _auth(client, "pharm_pat5")
    pat_id = _get_id(db_session, "pharm_pat5")
    r = client.post("/pharmacy/prescriptions", json={
        "patient_id": pat_id, "items": []
    }, headers=h)
    assert r.status_code == 400
    assert "item" in r.json()["detail"].lower()


def test_create_prescription_returns_404_for_unknown_patient(client, db_session):
    h = _auth(client, "pharm_admin5")
    _set_role(db_session, "pharm_admin5", "admin")
    r = client.post("/pharmacy/prescriptions", json={
        "patient_id": 99999,
        "items": [{"medication_name": "Aspirin", "dosage": "500mg",
                   "frequency": "BD", "duration": "5 days",
                   "quantity_prescribed": 10}]
    }, headers=h)
    assert r.status_code == 404


def test_pharmacy_metrics_requires_pharmacy_or_admin(client):
    h = _auth(client, "pharm_pat6")
    assert client.get("/pharmacy/admin/metrics", headers=h).status_code == 403


def test_pharmacy_metrics_returns_counts(client, db_session):
    h = _auth(client, "pharm_admin6")
    _set_role(db_session, "pharm_admin6", "admin")
    r = client.get("/pharmacy/admin/metrics", headers=h)
    assert r.status_code == 200
    data = r.json()
    assert "total_inventory_items" in data
    assert "total_prescriptions" in data
    assert "clinical_safety_note" in data


def test_dispense_returns_404_for_unknown_prescription(client, db_session):
    h = _auth(client, "pharm_admin7")
    _set_role(db_session, "pharm_admin7", "admin")
    r = client.post("/pharmacy/prescriptions/99999/dispense", json={"items": []}, headers=h)
    assert r.status_code == 404


def test_is_pharmacy_staff_true_for_pharmacist():
    u = models.User(username="p", hashed_password="x", role="pharmacist")
    assert pharmacy._is_pharmacy_staff(u) is True


def test_is_pharmacy_staff_false_for_patient():
    u = models.User(username="p", hashed_password="x", role="patient")
    assert pharmacy._is_pharmacy_staff(u) is False


def test_pharmacy_resolve_facility_mismatch_raises():
    e1 = models.MedicationInventory()
    e1.facility_id = 1
    e2 = models.MedicationInventory()
    e2.facility_id = 2
    with pytest.raises(HTTPException) as exc:
        pharmacy._resolve_pharmacy_facility_id(e1, e2)
    assert exc.value.status_code == 400
