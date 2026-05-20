import json

import pytest

from backend import auth, models


def _data_quality_module():
    try:
        from backend import data_quality
    except ImportError:
        pytest.fail("backend.data_quality module is required for data quality reporting")
    return data_quality


def _create_facility(db_session, name: str) -> models.HospitalFacility:
    facility = models.HospitalFacility(
        name=name,
        facility_type="hospital",
        country="India",
        status="active",
    )
    db_session.add(facility)
    db_session.commit()
    db_session.refresh(facility)
    return facility


def _create_user(db_session, username: str, role: str, facility_id: int | None = None) -> models.User:
    user = models.User(
        username=username,
        email=f"{username}@example.com",
        full_name=f"{role.title()} User",
        hashed_password=auth.get_password_hash("StrongPassword123!"),
        role=role,
        facility_id=facility_id,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def _auth_headers(username: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {auth.create_access_token({'sub': username})}"}


def test_data_quality_report_flags_invalid_vitals_without_pii(db_session):
    data_quality = _data_quality_module()
    facility = _create_facility(db_session, "Quality Facility")
    patient = _create_user(db_session, "quality_patient", "patient", facility.id)
    doctor = _create_user(db_session, "quality_doctor", "doctor", facility.id)
    db_session.add(models.VitalObservation(
        facility_id=facility.id,
        patient_id=patient.id,
        recorded_by_id=doctor.id,
        source="device",
        spo2=140,
        heart_rate=-5,
    ))
    db_session.commit()

    report = data_quality.generate_quality_report(db_session, facility_id=facility.id)

    checks = {check["id"]: check for check in report["checks"]}
    assert checks["vitals_spo2_range"]["status"] == "failed"
    assert checks["vitals_spo2_range"]["failed_count"] == 1
    assert checks["vitals_heart_rate_range"]["failed_count"] == 1
    assert report["overall_score"] < 1
    serialized = json.dumps(report)
    assert patient.username not in serialized
    assert patient.email not in serialized
    assert patient.full_name not in serialized


def test_data_quality_report_is_facility_scoped(db_session):
    data_quality = _data_quality_module()
    primary = _create_facility(db_session, "Quality Primary")
    other = _create_facility(db_session, "Quality Other")
    primary_patient = _create_user(db_session, "quality_primary_patient", "patient", primary.id)
    other_patient = _create_user(db_session, "quality_other_patient", "patient", other.id)
    db_session.add(models.VitalObservation(
        facility_id=primary.id,
        patient_id=primary_patient.id,
        source="manual",
        spo2=98,
        heart_rate=72,
    ))
    db_session.add(models.VitalObservation(
        facility_id=other.id,
        patient_id=other_patient.id,
        source="manual",
        spo2=180,
        heart_rate=72,
    ))
    db_session.commit()

    report = data_quality.generate_quality_report(db_session, facility_id=primary.id)

    checks = {check["id"]: check for check in report["checks"]}
    assert checks["vitals_spo2_range"]["failed_count"] == 0
    assert checks["vitals_spo2_range"]["total_count"] == 1


def test_data_quality_report_includes_lineage_for_core_datasets(db_session):
    data_quality = _data_quality_module()

    report = data_quality.generate_quality_report(db_session)

    datasets = {dataset["name"]: dataset for dataset in report["datasets"]}
    assert "patient_accounts" in datasets
    assert "vital_observations" in datasets
    assert "interoperability_exports" in datasets
    assert datasets["vital_observations"]["lineage"]["source_tables"] == ["vital_observations"]
    assert "monitoring.py" in datasets["vital_observations"]["lineage"]["upstream_modules"]
    assert all(dataset["pii_exposed"] is False for dataset in datasets.values())


def test_data_quality_report_includes_openlineage_events_and_quarantine_summary(db_session):
    data_quality = _data_quality_module()
    facility = _create_facility(db_session, "Lineage Facility")
    patient = _create_user(db_session, "lineage_patient", "patient", facility.id)
    doctor = _create_user(db_session, "lineage_doctor", "doctor", facility.id)
    db_session.add(models.VitalObservation(
        facility_id=facility.id,
        patient_id=patient.id,
        recorded_by_id=doctor.id,
        source="device",
        spo2=140,
        heart_rate=72,
    ))
    db_session.commit()

    report = data_quality.generate_quality_report(db_session, facility_id=facility.id)

    events = {event["job"]["name"]: event for event in report["lineage_events"]}
    vitals_event = events["data_quality.vital_observations"]
    assert vitals_event["eventType"] == "COMPLETE"
    assert vitals_event["producer"].endswith("backend.data_quality")
    assert vitals_event["schemaURL"].endswith("/RunEvent")
    assert vitals_event["run"]["runId"].startswith("data-quality-")
    assert vitals_event["inputs"] == [
        {"namespace": "ai-healthcare-system", "name": "vital_observations"}
    ]
    output = vitals_event["outputs"][0]
    assert output["name"] == "quality.vital_observations"
    assert output["facets"]["privacy"]["piiExposed"] is False
    metrics = output["facets"]["dataQualityMetrics"]
    assert metrics["rowCount"] == 1
    assert "vitals_spo2_range" in metrics["failedChecks"]

    quarantine = report["quarantine"]
    assert quarantine["enabled"] is True
    assert quarantine["record_level_payloads_exposed"] is False
    quarantine_entry = next(
        entry for entry in quarantine["datasets"]
        if entry["check_id"] == "vitals_spo2_range"
    )
    assert quarantine_entry["dataset"] == "vital_observations"
    assert quarantine_entry["failed_count"] == 1
    assert quarantine_entry["quarantine_table"] == "quarantine_vital_observations"

    serialized = json.dumps(report)
    assert patient.username not in serialized
    assert patient.email not in serialized
    assert patient.full_name not in serialized


def test_admin_reads_data_quality_report(client, db_session):
    facility = _create_facility(db_session, "Quality Admin Facility")
    admin = _create_user(db_session, "quality_admin", "admin", facility.id)
    patient = _create_user(db_session, "quality_admin_patient", "patient", facility.id)
    facility_id = facility.id
    patient_username = patient.username
    patient_email = patient.email
    db_session.add(models.Invoice(
        facility_id=facility_id,
        patient_id=patient.id,
        total_amount=-1,
        balance_amount=-1,
        currency="INR",
    ))
    db_session.commit()

    response = client.get("/admin/data-quality", headers=_auth_headers(admin.username))

    assert response.status_code == 200
    payload = response.json()
    checks = {check["id"]: check for check in payload["checks"]}
    assert payload["facility_id"] == facility_id
    assert checks["invoices_amounts_non_negative"]["failed_count"] == 1
    serialized = json.dumps(payload)
    assert patient_username not in serialized
    assert patient_email not in serialized


def test_patient_cannot_read_data_quality_report(client, db_session):
    patient = _create_user(db_session, "quality_patient_forbidden", "patient")

    response = client.get("/admin/data-quality", headers=_auth_headers(patient.username))

    assert response.status_code == 403
    assert response.json()["detail"] == "Admin privileges required"
