import json

import pytest

from backend import auth, models


def _operational_health_module():
    try:
        from backend import operational_health
    except ImportError:
        pytest.fail("backend.operational_health module is required for backend readiness reporting")
    return operational_health


def _create_user(db_session, username: str, role: str) -> models.User:
    user = models.User(
        username=username,
        email=f"{username}@example.com",
        full_name=f"{role.title()} User",
        hashed_password=auth.get_password_hash("StrongPassword123!"),
        role=role,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def _auth_headers(username: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {auth.create_access_token({'sub': username})}"}


def test_operational_health_report_returns_core_checks_without_pii(db_session):
    operational_health = _operational_health_module()
    patient = _create_user(db_session, "ops_health_patient", "patient")

    report = operational_health.build_operational_health_report(
        db_session,
        routes=[("GET", "/healthz"), ("GET", "/admin/data-quality")],
        facility_id=None,
    )

    check_ids = {check["id"] for check in report["checks"]}
    assert {
        "database_reachable",
        "duplicate_routes",
        "security_headers_expected",
        "ai_function_registry_valid",
        "data_quality_available",
        "abdm_readiness_available",
        "dicomweb_readiness_available",
        "smart_fhir_readiness_available",
        "backup_readiness_available",
        "incident_response_readiness_available",
        "retention_policy_readiness_available",
        "security_assurance_readiness_available",
    }.issubset(check_ids)
    assert report["status"] in {"healthy", "degraded"}
    serialized = json.dumps(report)
    assert patient.username not in serialized
    assert patient.email not in serialized
    assert patient.full_name not in serialized


def test_operational_health_detects_duplicate_routes(db_session):
    operational_health = _operational_health_module()

    report = operational_health.build_operational_health_report(
        db_session,
        routes=[("GET", "/healthz"), ("GET", "/healthz")],
        facility_id=None,
    )

    duplicate_check = {check["id"]: check for check in report["checks"]}["duplicate_routes"]
    assert duplicate_check["status"] == "failed"
    assert duplicate_check["failed_count"] == 1


def test_admin_reads_operational_health(client, db_session):
    admin = _create_user(db_session, "ops_health_admin", "admin")

    response = client.get("/admin/operational-health", headers=_auth_headers(admin.username))

    assert response.status_code == 200
    payload = response.json()
    assert payload["source"] == "backend.operational_health"
    assert any(check["id"] == "database_reachable" for check in payload["checks"])


def test_patient_cannot_read_operational_health(client, db_session):
    patient = _create_user(db_session, "ops_health_patient_forbidden", "patient")

    response = client.get("/admin/operational-health", headers=_auth_headers(patient.username))

    assert response.status_code == 403
    assert response.json()["detail"] == "Admin privileges required"
