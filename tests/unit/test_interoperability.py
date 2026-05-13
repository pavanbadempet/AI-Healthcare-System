import hashlib
import json

from backend import auth, models


def _create_user(
    db_session,
    username: str,
    role: str,
    *,
    facility_id: int | None = None,
) -> models.User:
    user = models.User(
        username=username,
        email=f"{username}@example.com",
        full_name=f"{role.title()} User",
        hashed_password=auth.get_password_hash("StrongPassword123!"),
        role=role,
        allow_data_collection=1,
        facility_id=facility_id,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def _auth_headers(username: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {auth.create_access_token({'sub': username})}"}


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


def _create_export_context(
    db_session,
    patient_id: int,
    doctor_id: int,
    *,
    facility_id: int | None = None,
) -> models.Encounter:
    department = models.Department(
        name=f"Interop Department {patient_id}-{doctor_id}",
        facility_id=facility_id,
        department_type="OPD",
        status="active",
    )
    db_session.add(department)
    db_session.flush()
    encounter = models.Encounter(
        facility_id=facility_id,
        patient_id=patient_id,
        doctor_id=doctor_id,
        department_id=department.id,
        encounter_type="OPD",
        reason="Interoperability export",
        status="open",
    )
    db_session.add(encounter)
    db_session.flush()
    db_session.add(models.VitalObservation(
        facility_id=facility_id,
        patient_id=patient_id,
        recorded_by_id=doctor_id,
        encounter_id=encounter.id,
        department_id=department.id,
        source="manual",
        heart_rate=72,
        spo2=98,
    ))
    db_session.add(models.CareEvent(
        facility_id=facility_id,
        patient_id=patient_id,
        actor_user_id=doctor_id,
        encounter_id=encounter.id,
        department_id=department.id,
        event_type="SYNTHETIC_INTEROP_EVENT",
        title="Synthetic interoperability event",
        summary="Synthetic event summary for export tests.",
        severity="info",
    ))
    db_session.commit()
    db_session.refresh(encounter)
    return encounter


def test_terminology_lookup_requires_authentication(client):
    response = client.get("/interop/terminology/lookup?system=loinc&code=8867-4")

    assert response.status_code == 401


def test_authenticated_user_can_lookup_seed_terminology(client, db_session):
    user = _create_user(db_session, "interop_terminology_user", "doctor")

    response = client.get(
        "/interop/terminology/lookup?system=loinc&code=8867-4",
        headers=_auth_headers(user.username),
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["coding"] == {
        "system": "http://loinc.org",
        "code": "8867-4",
        "display": "Heart rate",
    }
    assert payload["source"] == "static_seed_catalog"


def test_terminology_lookup_returns_404_for_unknown_code(client, db_session):
    user = _create_user(db_session, "interop_terminology_unknown", "doctor")

    response = client.get(
        "/interop/terminology/lookup?system=loinc&code=not-a-code",
        headers=_auth_headers(user.username),
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Terminology code not found"


def test_dicomweb_readiness_is_admin_only(client, db_session, monkeypatch):
    doctor = _create_user(db_session, "interop_dicom_doctor", "doctor")
    admin = _create_user(db_session, "interop_dicom_admin", "admin")
    monkeypatch.setenv("DICOMWEB_ENABLED", "true")
    monkeypatch.setenv("DICOMWEB_BASE_URL", "https://pacs.example.com/dicomweb")
    monkeypatch.setenv("DICOMWEB_BEARER_TOKEN", "dicom-secret-token")

    forbidden = client.get("/interop/dicomweb/readiness", headers=_auth_headers(doctor.username))
    allowed = client.get("/interop/dicomweb/readiness", headers=_auth_headers(admin.username))

    assert forbidden.status_code == 403
    assert allowed.status_code == 200
    payload = allowed.json()
    assert payload["enabled"] is True
    assert payload["secrets_exposed"] is False
    assert "dicom-secret-token" not in json.dumps(payload)


def test_dicomweb_metadata_links_are_admin_only_and_validate_uid(client, db_session, monkeypatch):
    doctor = _create_user(db_session, "interop_dicom_link_doctor", "doctor")
    admin = _create_user(db_session, "interop_dicom_link_admin", "admin")
    monkeypatch.setenv("DICOMWEB_BASE_URL", "https://pacs.example.com/dicomweb")

    forbidden = client.get(
        "/interop/dicomweb/studies/1.2.840.10008.1/metadata-links",
        headers=_auth_headers(doctor.username),
    )
    invalid = client.get(
        "/interop/dicomweb/studies/not-a-uid/metadata-links",
        headers=_auth_headers(admin.username),
    )
    allowed = client.get(
        "/interop/dicomweb/studies/1.2.840.10008.1/metadata-links",
        headers=_auth_headers(admin.username),
    )

    assert forbidden.status_code == 403
    assert invalid.status_code == 400
    assert allowed.status_code == 200
    payload = allowed.json()
    assert payload["wado_rs_study_metadata"].endswith("/studies/1.2.840.10008.1/metadata")
    assert payload["pixel_data_included"] is False
    assert payload["pii_exposed"] is False


def test_smart_fhir_readiness_is_admin_only(client, db_session, monkeypatch):
    doctor = _create_user(db_session, "interop_smart_doctor", "doctor")
    admin = _create_user(db_session, "interop_smart_admin", "admin")
    monkeypatch.setenv("SMART_FHIR_ENABLED", "true")
    monkeypatch.setenv("SMART_AUTHORIZATION_ENDPOINT", "https://ehr.example.com/auth")
    monkeypatch.setenv("SMART_TOKEN_ENDPOINT", "https://ehr.example.com/token")
    monkeypatch.setenv("SMART_CLIENT_ID", "client-123")
    monkeypatch.setenv("SMART_CLIENT_SECRET", "smart-secret")
    monkeypatch.setenv("SMART_REDIRECT_URI", "https://app.example.com/callback")

    forbidden = client.get("/interop/smart/readiness", headers=_auth_headers(doctor.username))
    allowed = client.get("/interop/smart/readiness", headers=_auth_headers(admin.username))

    assert forbidden.status_code == 403
    assert allowed.status_code == 200
    payload = allowed.json()
    assert payload["enabled"] is True
    assert payload["secrets_exposed"] is False
    assert "smart-secret" not in json.dumps(payload)


def test_smart_fhir_authorize_url_is_admin_only_and_validates_state(client, db_session, monkeypatch):
    doctor = _create_user(db_session, "interop_smart_url_doctor", "doctor")
    admin = _create_user(db_session, "interop_smart_url_admin", "admin")
    monkeypatch.setenv("SMART_FHIR_BASE_URL", "https://ehr.example.com/fhir")
    monkeypatch.setenv("SMART_AUTHORIZATION_ENDPOINT", "https://ehr.example.com/auth")
    monkeypatch.setenv("SMART_CLIENT_ID", "client-123")
    monkeypatch.setenv("SMART_REDIRECT_URI", "https://app.example.com/callback")

    forbidden = client.get(
        "/interop/smart/authorize-url?state=state-123",
        headers=_auth_headers(doctor.username),
    )
    invalid = client.get(
        "/interop/smart/authorize-url?state=patient_name=Sensitive",
        headers=_auth_headers(admin.username),
    )
    allowed = client.get(
        "/interop/smart/authorize-url?state=state-123&launch=launch-123",
        headers=_auth_headers(admin.username),
    )

    assert forbidden.status_code == 403
    assert invalid.status_code == 400
    assert allowed.status_code == 200
    payload = allowed.json()
    assert payload["authorization_url"].startswith("https://ehr.example.com/auth?")
    assert payload["secrets_exposed"] is False
    assert "client_secret" not in json.dumps(payload).lower()


def _add_department_context(
    db_session,
    *,
    patient_id: int,
    doctor_id: int,
    department_name: str,
    event_title: str,
) -> models.Encounter:
    department = models.Department(
        name=department_name,
        department_type="IPD",
        status="active",
    )
    db_session.add(department)
    db_session.flush()
    encounter = models.Encounter(
        patient_id=patient_id,
        doctor_id=doctor_id,
        department_id=department.id,
        encounter_type="IPD",
        reason=f"{department_name} export",
        status="open",
    )
    db_session.add(encounter)
    db_session.flush()
    db_session.add(models.VitalObservation(
        patient_id=patient_id,
        recorded_by_id=doctor_id,
        encounter_id=encounter.id,
        department_id=department.id,
        source="manual",
        heart_rate=88,
        spo2=96,
    ))
    db_session.add(models.CareEvent(
        patient_id=patient_id,
        actor_user_id=doctor_id,
        encounter_id=encounter.id,
        department_id=department.id,
        event_type="SYNTHETIC_DEPARTMENT_EVENT",
        title=event_title,
        summary="Synthetic department event summary.",
        severity="info",
    ))
    db_session.commit()
    db_session.refresh(encounter)
    return encounter


def _grant_export_consent(client, patient_username: str, purpose: str = "Share records with assigned care team") -> dict:
    response = client.post(
        "/interop/patient/consents",
        json={
            "scope": "fhir_bundle_export",
            "purpose": purpose,
            "recipient_type": "care_team",
        },
        headers=_auth_headers(patient_username),
    )
    assert response.status_code == 201
    return response.json()


def _create_export_profile(
    client,
    admin_username: str,
    *,
    name: str = "Referral Summary Profile",
    resource_types: list[str] | None = None,
    department_id: int | None = None,
) -> dict:
    payload = {
        "name": name,
        "partner_system": "Partner HIS",
        "resource_types": resource_types if resource_types is not None else ["Observation", "CareEvent"],
        "department_id": department_id,
    }
    response = client.post(
        "/interop/admin/export-profiles",
        json=payload,
        headers=_auth_headers(admin_username),
    )
    assert response.status_code == 201
    return response.json()


def _resource_types(bundle: dict) -> list[str]:
    return [entry["resource"]["resourceType"] for entry in bundle["entry"]]


def _first_resource(bundle: dict, resource_type: str) -> dict:
    for entry in bundle["entry"]:
        resource = entry["resource"]
        if resource["resourceType"] == resource_type:
            return resource
    raise AssertionError(f"Missing {resource_type} resource")


def _bundle_sha256(bundle: dict) -> str:
    canonical = json.dumps(bundle, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def test_patient_exports_own_fhir_style_bundle(client, db_session):
    patient = _create_user(db_session, "interop_patient", "patient")
    doctor = _create_user(db_session, "interop_doctor", "doctor")
    patient_username = patient.username
    patient_id = patient.id
    doctor_id = doctor.id
    _create_export_context(db_session, patient_id, doctor_id)

    response = client.get("/interop/patient/fhir-bundle", headers=_auth_headers(patient_username))

    assert response.status_code == 200
    payload = response.json()
    assert payload["bundle"]["resourceType"] == "Bundle"
    assert payload["export"]["patient_id"] == patient_id
    assert "certified" not in payload["standards_note"].lower()
    resource_types = _resource_types(payload["bundle"])
    assert "Patient" in resource_types
    assert "Encounter" in resource_types
    assert "Observation" in resource_types
    export_log = db_session.query(models.InteroperabilityExport).one()
    assert export_log.patient_id == patient_id
    assert export_log.resource_count == len(resource_types)


def test_patient_bundle_uses_validated_fhir_resource_shapes(client, db_session):
    patient = _create_user(db_session, "interop_fhir_shape_patient", "patient")
    doctor = _create_user(db_session, "interop_fhir_shape_doctor", "doctor")
    _create_export_context(db_session, patient.id, doctor.id)

    response = client.get("/interop/patient/fhir-bundle", headers=_auth_headers(patient.username))

    assert response.status_code == 200
    bundle = response.json()["bundle"]
    patient_resource = _first_resource(bundle, "Patient")
    observation_resource = _first_resource(bundle, "Observation")
    assert "telecom" not in patient_resource
    assert patient_resource["identifier"] == [
        {"system": "ai-healthcare-system:user-id", "value": str(patient.id)}
    ]
    assert observation_resource["component"][0]["code"]["coding"][0] == {
        "system": "http://loinc.org",
        "code": "8867-4",
        "display": "Heart rate",
    }
    assert observation_resource["component"][0]["valueQuantity"]["system"] == "http://unitsofmeasure.org"


def test_patient_export_log_persists_facility_id(client, db_session):
    facility = _create_facility(db_session, "Interop Export Facility")
    facility_id = facility.id
    patient = _create_user(db_session, "interop_facility_patient", "patient", facility_id=facility_id)
    doctor = _create_user(db_session, "interop_facility_doctor", "doctor", facility_id=facility_id)
    patient_username = patient.username
    patient_id = patient.id
    doctor_id = doctor.id
    _create_export_context(db_session, patient_id, doctor_id, facility_id=facility_id)

    response = client.get("/interop/patient/fhir-bundle", headers=_auth_headers(patient_username))

    assert response.status_code == 200
    assert response.json()["export"]["facility_id"] == facility_id
    export_log = db_session.query(models.InteroperabilityExport).one()
    assert export_log.facility_id == facility_id


def test_facility_admin_cannot_export_other_facility_patient_bundle(client, db_session):
    primary_facility = _create_facility(db_session, "Interop Admin Primary")
    other_facility = _create_facility(db_session, "Interop Admin Other")
    admin = _create_user(db_session, "interop_facility_admin", "admin", facility_id=primary_facility.id)
    patient = _create_user(db_session, "interop_other_facility_patient", "patient", facility_id=other_facility.id)
    doctor = _create_user(db_session, "interop_other_facility_doctor", "doctor", facility_id=other_facility.id)
    admin_username = admin.username
    patient_username = patient.username
    patient_id = patient.id
    doctor_id = doctor.id
    _create_export_context(db_session, patient_id, doctor_id, facility_id=other_facility.id)
    _grant_export_consent(client, patient_username)

    response = client.get(
        f"/interop/doctor/patients/{patient_id}/fhir-bundle",
        headers=_auth_headers(admin_username),
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Interoperability resource is outside the user's facility"


def test_export_response_includes_signed_manifest(client, db_session):
    patient = _create_user(db_session, "interop_manifest_patient", "patient")
    doctor = _create_user(db_session, "interop_manifest_doctor", "doctor")
    patient_username = patient.username
    patient_id = patient.id
    _create_export_context(db_session, patient_id, doctor.id)

    response = client.get("/interop/patient/fhir-bundle", headers=_auth_headers(patient_username))

    assert response.status_code == 200
    payload = response.json()
    manifest = payload["manifest"]
    assert manifest["resourceType"] == "ExportManifest"
    assert manifest["patient_id"] == patient_id
    assert manifest["export_id"] == payload["export"]["id"]
    assert manifest["bundle_sha256"] == _bundle_sha256(payload["bundle"])
    assert manifest["signature_algorithm"] == "HMAC-SHA256"
    assert len(manifest["signature"]) == 64
    assert payload["export"]["bundle_sha256"] == manifest["bundle_sha256"]
    assert payload["export"]["manifest_signature"] == manifest["signature"]
    export_log = db_session.query(models.InteroperabilityExport).one()
    assert export_log.bundle_sha256 == manifest["bundle_sha256"]
    assert export_log.manifest_signature == manifest["signature"]


def test_patient_filters_bundle_by_resource_types(client, db_session):
    patient = _create_user(db_session, "interop_filter_patient", "patient")
    doctor = _create_user(db_session, "interop_filter_doctor", "doctor")
    patient_username = patient.username
    patient_id = patient.id
    _create_export_context(db_session, patient_id, doctor.id)

    response = client.get(
        "/interop/patient/fhir-bundle?resource_types=Observation,CareEvent",
        headers=_auth_headers(patient_username),
    )

    assert response.status_code == 200
    payload = response.json()
    assert _resource_types(payload["bundle"]) == ["Patient", "Observation", "CareEvent"]
    assert payload["filters"]["resource_types"] == ["Observation", "CareEvent"]
    assert payload["manifest"]["filters"]["resource_types"] == ["Observation", "CareEvent"]
    export_log = db_session.query(models.InteroperabilityExport).one()
    assert json.loads(export_log.filter_summary)["resource_types"] == ["Observation", "CareEvent"]


def test_patient_filters_bundle_by_department(client, db_session):
    patient = _create_user(db_session, "interop_department_filter_patient", "patient")
    doctor = _create_user(db_session, "interop_department_filter_doctor", "doctor")
    patient_username = patient.username
    patient_id = patient.id
    doctor_id = doctor.id
    target_encounter = _add_department_context(
        db_session,
        patient_id=patient_id,
        doctor_id=doctor_id,
        department_name="Cardiology Filter Department",
        event_title="Target department event",
    )
    _add_department_context(
        db_session,
        patient_id=patient_id,
        doctor_id=doctor_id,
        department_name="Neurology Filter Department",
        event_title="Other department event",
    )
    target_department_id = target_encounter.department_id

    response = client.get(
        f"/interop/patient/fhir-bundle?department_id={target_department_id}",
        headers=_auth_headers(patient_username),
    )

    assert response.status_code == 200
    payload = response.json()
    serialized = json.dumps(payload["bundle"])
    assert "Target department event" in serialized
    assert "Other department event" not in serialized
    assert payload["filters"]["department_id"] == target_department_id
    assert payload["manifest"]["filters"]["department_id"] == target_department_id


def test_patient_export_rejects_unknown_resource_filter(client, db_session):
    patient = _create_user(db_session, "interop_invalid_filter_patient", "patient")
    patient_username = patient.username

    response = client.get(
        "/interop/patient/fhir-bundle?resource_types=Observation,UnknownResource",
        headers=_auth_headers(patient_username),
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Unsupported interoperability resource type: UnknownResource"


def test_patient_export_validation_failure_does_not_record_export(client, db_session):
    patient = _create_user(db_session, "interop_invalid_fhir_patient", "patient")
    doctor = _create_user(db_session, "interop_invalid_fhir_doctor", "doctor")
    department = models.Department(
        name="Invalid FHIR Department",
        department_type="OPD",
        status="active",
    )
    db_session.add(department)
    db_session.flush()
    encounter = models.Encounter(
        patient_id=patient.id,
        doctor_id=doctor.id,
        department_id=department.id,
        encounter_type="OPD",
        reason="Invalid FHIR validation",
        status="open",
    )
    db_session.add(encounter)
    db_session.flush()
    db_session.add(models.VitalObservation(
        patient_id=patient.id,
        recorded_by_id=doctor.id,
        encounter_id=encounter.id,
        department_id=department.id,
        source="manual",
    ))
    db_session.commit()

    response = client.get(
        "/interop/patient/fhir-bundle?resource_types=Observation",
        headers=_auth_headers(patient.username),
    )

    assert response.status_code == 422
    assert response.json()["detail"] == "Generated FHIR bundle failed validation"
    assert db_session.query(models.InteroperabilityExport).count() == 0


def test_admin_creates_and_lists_export_profile(client, db_session):
    admin = _create_user(db_session, "interop_profile_admin", "admin")
    admin_username = admin.username

    profile = _create_export_profile(
        client,
        admin_username,
        name="Cardiology Referral Profile",
        resource_types=["Observation", "CareEvent"],
    )

    assert profile["name"] == "Cardiology Referral Profile"
    assert profile["partner_system"] == "Partner HIS"
    assert profile["resource_types"] == ["Observation", "CareEvent"]
    assert profile["status"] == "active"
    profile_log = db_session.query(models.InteroperabilityExportProfile).one()
    assert profile_log.name == "Cardiology Referral Profile"

    response = client.get("/interop/admin/export-profiles", headers=_auth_headers(admin_username))

    assert response.status_code == 200
    assert response.json()[0]["id"] == profile["id"]


def test_patient_cannot_create_export_profile(client, db_session):
    patient = _create_user(db_session, "interop_profile_patient", "patient")

    response = client.post(
        "/interop/admin/export-profiles",
        json={
            "name": "Unauthorized Profile",
            "partner_system": "Partner HIS",
            "resource_types": ["Observation"],
        },
        headers=_auth_headers(patient.username),
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Admin privileges required"


def test_export_uses_saved_profile_filters(client, db_session):
    admin = _create_user(db_session, "interop_profile_export_admin", "admin")
    patient = _create_user(db_session, "interop_profile_export_patient", "patient")
    doctor = _create_user(db_session, "interop_profile_export_doctor", "doctor")
    admin_username = admin.username
    patient_username = patient.username
    doctor_username = doctor.username
    patient_id = patient.id
    doctor_id = doctor.id
    _create_export_context(db_session, patient_id, doctor_id)
    _grant_export_consent(client, patient_username)
    profile = _create_export_profile(
        client,
        admin_username,
        name="Vitals And Timeline Profile",
        resource_types=["Observation", "CareEvent"],
    )

    response = client.get(
        f"/interop/doctor/patients/{patient_id}/fhir-bundle?profile_id={profile['id']}",
        headers=_auth_headers(doctor_username),
    )

    assert response.status_code == 200
    payload = response.json()
    assert _resource_types(payload["bundle"]) == ["Patient", "Observation", "CareEvent"]
    assert payload["filters"]["profile_id"] == profile["id"]
    assert payload["filters"]["profile_name"] == "Vitals And Timeline Profile"
    assert payload["manifest"]["filters"]["profile_id"] == profile["id"]
    export_log = db_session.query(models.InteroperabilityExport).one()
    assert export_log.profile_id == profile["id"]
    assert json.loads(export_log.filter_summary)["profile_id"] == profile["id"]


def test_assigned_doctor_exports_patient_bundle(client, db_session):
    doctor = _create_user(db_session, "interop_assigned_doctor", "doctor")
    patient = _create_user(db_session, "interop_doctor_patient", "patient")
    doctor_username = doctor.username
    patient_username = patient.username
    doctor_id = doctor.id
    patient_id = patient.id
    _create_export_context(db_session, patient_id, doctor_id)
    consent = _grant_export_consent(client, patient_username)

    response = client.get(
        f"/interop/doctor/patients/{patient_id}/fhir-bundle",
        headers=_auth_headers(doctor_username),
    )

    assert response.status_code == 200
    assert response.json()["patient_id"] == patient_id
    assert response.json()["export"]["consent_id"] == consent["id"]
    assert "CareEvent" in _resource_types(response.json()["bundle"])


def test_admin_retrieves_export_manifest(client, db_session):
    admin = _create_user(db_session, "interop_manifest_admin", "admin")
    doctor = _create_user(db_session, "interop_manifest_admin_doctor", "doctor")
    patient = _create_user(db_session, "interop_manifest_admin_patient", "patient")
    patient_username = patient.username
    admin_username = admin.username
    patient_id = patient.id
    _create_export_context(db_session, patient_id, doctor.id)
    _grant_export_consent(client, patient_username)
    export_response = client.get(
        f"/interop/doctor/patients/{patient_id}/fhir-bundle",
        headers=_auth_headers(admin_username),
    )
    export_id = export_response.json()["export"]["id"]
    expected_hash = export_response.json()["manifest"]["bundle_sha256"]

    response = client.get(f"/interop/exports/{export_id}/manifest", headers=_auth_headers(admin_username))

    assert response.status_code == 200
    manifest = response.json()
    assert manifest["export_id"] == export_id
    assert manifest["bundle_sha256"] == expected_hash
    assert "bundle" not in manifest


def test_other_patient_cannot_read_export_manifest(client, db_session):
    patient = _create_user(db_session, "interop_manifest_owner", "patient")
    other_patient = _create_user(db_session, "interop_manifest_other", "patient")
    doctor = _create_user(db_session, "interop_manifest_owner_doctor", "doctor")
    patient_username = patient.username
    other_username = other_patient.username
    patient_id = patient.id
    doctor_id = doctor.id
    _create_export_context(db_session, patient_id, doctor_id)
    export_response = client.get("/interop/patient/fhir-bundle", headers=_auth_headers(patient_username))
    export_id = export_response.json()["export"]["id"]

    response = client.get(f"/interop/exports/{export_id}/manifest", headers=_auth_headers(other_username))

    assert response.status_code == 403
    assert response.json()["detail"] == "You cannot access this export manifest"


def test_assigned_doctor_cannot_export_without_active_consent(client, db_session):
    doctor = _create_user(db_session, "interop_no_consent_doctor", "doctor")
    patient = _create_user(db_session, "interop_no_consent_patient", "patient")
    doctor_username = doctor.username
    patient_id = patient.id
    _create_export_context(db_session, patient_id, doctor.id)

    response = client.get(
        f"/interop/doctor/patients/{patient_id}/fhir-bundle",
        headers=_auth_headers(doctor_username),
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Active interoperability consent required"


def test_unassigned_doctor_cannot_export_patient_bundle(client, db_session):
    assigned_doctor = _create_user(db_session, "interop_private_assigned", "doctor")
    other_doctor = _create_user(db_session, "interop_private_other", "doctor")
    patient = _create_user(db_session, "interop_private_patient", "patient")
    other_username = other_doctor.username
    patient_id = patient.id
    _create_export_context(db_session, patient_id, assigned_doctor.id)

    response = client.get(
        f"/interop/doctor/patients/{patient_id}/fhir-bundle",
        headers=_auth_headers(other_username),
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Doctor is not assigned to this patient"


def test_patient_cannot_access_interoperability_metrics(client, db_session):
    patient = _create_user(db_session, "interop_metrics_patient", "patient")
    patient_username = patient.username

    response = client.get("/interop/admin/metrics", headers=_auth_headers(patient_username))

    assert response.status_code == 403
    assert response.json()["detail"] == "Admin privileges required"


def test_patient_grants_and_lists_interoperability_consent(client, db_session):
    patient = _create_user(db_session, "interop_consent_patient", "patient")
    patient_username = patient.username
    patient_id = patient.id

    consent = _grant_export_consent(client, patient_username, purpose="Referral export to cardiology")

    assert consent["patient_id"] == patient_id
    assert consent["scope"] == "fhir_bundle_export"
    assert consent["status"] == "active"
    assert "certified" not in consent["standards_note"].lower()
    consent_log = db_session.query(models.InteroperabilityConsent).one()
    assert consent_log.patient_id == patient_id
    assert consent_log.purpose == "Referral export to cardiology"

    response = client.get("/interop/patient/consents", headers=_auth_headers(patient_username))

    assert response.status_code == 200
    assert response.json()[0]["id"] == consent["id"]


def test_revoked_consent_blocks_doctor_export(client, db_session):
    doctor = _create_user(db_session, "interop_revoked_doctor", "doctor")
    patient = _create_user(db_session, "interop_revoked_patient", "patient")
    patient_username = patient.username
    patient_id = patient.id
    doctor_username = doctor.username
    _create_export_context(db_session, patient_id, doctor.id)
    consent = _grant_export_consent(client, patient_username)

    revoke = client.post(
        f"/interop/patient/consents/{consent['id']}/revoke",
        headers=_auth_headers(patient_username),
    )
    assert revoke.status_code == 200
    assert revoke.json()["status"] == "revoked"

    response = client.get(
        f"/interop/doctor/patients/{patient_id}/fhir-bundle",
        headers=_auth_headers(doctor_username),
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Active interoperability consent required"


def test_assigned_doctor_views_patient_consent_status(client, db_session):
    doctor = _create_user(db_session, "interop_status_doctor", "doctor")
    patient = _create_user(db_session, "interop_status_patient", "patient")
    patient_username = patient.username
    patient_id = patient.id
    doctor_username = doctor.username
    _create_export_context(db_session, patient_id, doctor.id)
    consent = _grant_export_consent(client, patient_username)

    response = client.get(
        f"/interop/doctor/patients/{patient_id}/consent-status",
        headers=_auth_headers(doctor_username),
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["patient_id"] == patient_id
    assert payload["has_active_consent"] is True
    assert payload["active_consent"]["id"] == consent["id"]


def test_admin_interoperability_metrics(client, db_session):
    admin = _create_user(db_session, "interop_admin", "admin")
    patient = _create_user(db_session, "interop_admin_patient", "patient")
    doctor = _create_user(db_session, "interop_admin_doctor", "doctor")
    admin_username = admin.username
    patient_username = patient.username
    patient_id = patient.id
    doctor_id = doctor.id
    _create_export_context(db_session, patient_id, doctor_id)
    _grant_export_consent(client, patient_username)
    client.get(f"/interop/doctor/patients/{patient_id}/fhir-bundle", headers=_auth_headers(admin_username))

    response = client.get("/interop/admin/metrics", headers=_auth_headers(admin_username))

    assert response.status_code == 200
    payload = response.json()
    assert payload["total_exports"] == 1
    assert payload["exports_by_type"]["fhir_bundle"] == 1
    assert payload["total_resources_exported"] >= 3


def test_interoperability_metrics_are_facility_scoped_for_assigned_admin(client, db_session):
    primary_facility = _create_facility(db_session, "Interop Metrics Primary")
    other_facility = _create_facility(db_session, "Interop Metrics Other")
    primary_id = primary_facility.id
    other_id = other_facility.id
    admin = _create_user(db_session, "interop_metrics_facility_admin", "admin", facility_id=primary_id)
    other_admin = _create_user(db_session, "interop_metrics_other_admin", "admin", facility_id=other_id)
    patient = _create_user(db_session, "interop_metrics_facility_patient", "patient", facility_id=primary_id)
    other_patient = _create_user(db_session, "interop_metrics_other_patient", "patient", facility_id=other_id)
    doctor = _create_user(db_session, "interop_metrics_facility_doctor", "doctor", facility_id=primary_id)
    other_doctor = _create_user(db_session, "interop_metrics_other_doctor", "doctor", facility_id=other_id)
    admin_username = admin.username
    other_admin_username = other_admin.username
    patient_username = patient.username
    other_patient_username = other_patient.username
    patient_id = patient.id
    other_patient_id = other_patient.id
    doctor_id = doctor.id
    other_doctor_id = other_doctor.id
    _create_export_context(db_session, patient_id, doctor_id, facility_id=primary_id)
    _create_export_context(db_session, other_patient_id, other_doctor_id, facility_id=other_id)
    _grant_export_consent(client, patient_username)
    _grant_export_consent(client, other_patient_username)
    client.get(f"/interop/doctor/patients/{patient_id}/fhir-bundle", headers=_auth_headers(admin_username))
    client.get(
        f"/interop/doctor/patients/{other_patient_id}/fhir-bundle",
        headers=_auth_headers(other_admin_username),
    )

    response = client.get("/interop/admin/metrics", headers=_auth_headers(admin_username))

    assert response.status_code == 200
    payload = response.json()
    assert payload["total_exports"] == 1
    assert payload["exports_by_type"]["fhir_bundle"] == 1
    assert payload["active_consents"] == 1


def test_admin_views_abdm_readiness_without_secret(client, db_session, monkeypatch):
    monkeypatch.setenv("ABDM_ENABLED", "true")
    monkeypatch.setenv("ABDM_CLIENT_SECRET", "synthetic-secret-value")
    monkeypatch.delenv("ABDM_BASE_URL", raising=False)
    admin = _create_user(db_session, "interop_abdm_admin", "admin")

    response = client.get("/interop/abdm/readiness", headers=_auth_headers(admin.username))

    assert response.status_code == 200
    payload = response.json()
    assert payload["configured"] is False
    assert "ABDM_BASE_URL" in payload["missing"]
    assert "synthetic-secret-value" not in json.dumps(payload)


def test_patient_cannot_view_abdm_readiness(client, db_session):
    patient = _create_user(db_session, "interop_abdm_readiness_patient", "patient")

    response = client.get("/interop/abdm/readiness", headers=_auth_headers(patient.username))

    assert response.status_code == 403
    assert response.json()["detail"] == "Admin privileges required"


def test_assigned_doctor_prepares_abdm_consent_request(client, db_session, monkeypatch):
    monkeypatch.setenv("ABDM_HIU_ID", "AIH-HIU")
    doctor = _create_user(db_session, "interop_abdm_doctor", "doctor")
    patient = _create_user(db_session, "interop_abdm_patient", "patient")
    _create_export_context(db_session, patient.id, doctor.id)

    response = client.post(
        "/interop/abdm/consent-requests",
        json={
            "patient_id": patient.id,
            "patient_abha_address": "synthetic@sbx",
            "purpose_code": "CAREMGT",
            "hi_types": ["DiagnosticReport"],
            "date_from": "2026-05-01T00:00:00Z",
            "date_to": "2026-05-27T00:00:00Z",
            "data_erase_at": "2026-06-26T00:00:00Z",
            "submit": False,
        },
        headers=_auth_headers(doctor.username),
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["patient_id"] == patient.id
    assert payload["submitted"] is False
    assert payload["payload"]["consent"]["patient"]["id"] == "synthetic@sbx"
    assert payload["payload"]["consent"]["hiu"]["id"] == "AIH-HIU"
    assert payload["payload"]["consent"]["hiTypes"] == ["DiagnosticReport"]


def test_unassigned_doctor_cannot_prepare_abdm_consent_request(client, db_session):
    assigned_doctor = _create_user(db_session, "interop_abdm_assigned_doctor", "doctor")
    other_doctor = _create_user(db_session, "interop_abdm_other_doctor", "doctor")
    patient = _create_user(db_session, "interop_abdm_private_patient", "patient")
    _create_export_context(db_session, patient.id, assigned_doctor.id)

    response = client.post(
        "/interop/abdm/consent-requests",
        json={
            "patient_id": patient.id,
            "patient_abha_address": "synthetic@sbx",
            "purpose_code": "CAREMGT",
            "hi_types": ["DiagnosticReport"],
            "date_from": "2026-05-01T00:00:00Z",
            "date_to": "2026-05-27T00:00:00Z",
            "data_erase_at": "2026-06-26T00:00:00Z",
            "submit": False,
        },
        headers=_auth_headers(other_doctor.username),
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Doctor is not assigned to this patient"


def test_admin_records_abdm_consent_callback_and_updates_local_consent(client, db_session):
    facility = _create_facility(db_session, "Interop ABDM Callback Facility")
    admin = _create_user(db_session, "interop_abdm_callback_admin", "admin", facility_id=facility.id)
    patient = _create_user(db_session, "interop_abdm_callback_patient", "patient", facility_id=facility.id)
    consent = models.InteroperabilityConsent(
        facility_id=facility.id,
        patient_id=patient.id,
        granted_by_id=patient.id,
        scope="fhir_bundle_export",
        purpose="ABDM callback tracking",
        recipient_type="abdm_hiu",
        status="requested",
    )
    db_session.add(consent)
    db_session.commit()
    db_session.refresh(consent)
    facility_id = facility.id
    admin_id = admin.id
    patient_id = patient.id
    consent_id = consent.id
    patient_username = patient.username
    patient_email = patient.email

    response = client.post(
        "/interop/abdm/consent-callbacks",
        json={
            "patient_id": patient_id,
            "local_consent_id": consent_id,
            "abdm_request_id": "request-123",
            "abdm_consent_id": "consent-123",
            "status": "GRANTED",
            "hi_types": ["DiagnosticReport"],
            "event_type": "consent_status",
            "notification_at": "2026-05-28T08:00:00Z",
        },
        headers=_auth_headers(admin.username),
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["source"] == "backend.abdm"
    assert payload["facility_id"] == facility_id
    assert payload["patient_id"] == patient_id
    assert payload["local_consent_id"] == consent_id
    assert payload["status"] == "GRANTED"
    assert payload["local_consent_status"] == "active"
    assert payload["raw_payload_stored"] is False
    assert patient_username not in response.text
    assert patient_email not in response.text
    event = db_session.query(models.ABDMConsentEvent).one()
    assert event.facility_id == facility_id
    assert event.patient_id == patient_id
    assert event.local_consent_id == consent_id
    assert event.abdm_request_id == "request-123"
    assert event.abdm_consent_id == "consent-123"
    assert event.status == "GRANTED"
    assert len(event.payload_sha256) == 64
    updated_consent = db_session.get(models.InteroperabilityConsent, consent_id)
    assert updated_consent.status == "active"
    assert updated_consent.abdm_request_id == "request-123"
    assert updated_consent.abdm_consent_id == "consent-123"
    assert updated_consent.abdm_status == "GRANTED"
    audit_entry = db_session.query(models.AuditLog).filter(
        models.AuditLog.admin_id == admin_id,
        models.AuditLog.target_user_id == patient_id,
        models.AuditLog.action == "ABDM_CONSENT_CALLBACK",
    ).one()
    assert audit_entry.facility_id == facility_id
    assert "abdm_consent_event" in audit_entry.details
    assert patient_username not in audit_entry.details
    assert patient_email not in audit_entry.details


def test_facility_admin_cannot_record_abdm_callback_for_other_facility_consent(client, db_session):
    primary = _create_facility(db_session, "Interop ABDM Callback Primary")
    other = _create_facility(db_session, "Interop ABDM Callback Other")
    admin = _create_user(db_session, "interop_abdm_callback_facility_admin", "admin", facility_id=primary.id)
    patient = _create_user(db_session, "interop_abdm_callback_other_patient", "patient", facility_id=other.id)
    consent = models.InteroperabilityConsent(
        facility_id=other.id,
        patient_id=patient.id,
        granted_by_id=patient.id,
        scope="fhir_bundle_export",
        purpose="ABDM callback tracking",
        recipient_type="abdm_hiu",
        status="requested",
    )
    db_session.add(consent)
    db_session.commit()
    db_session.refresh(consent)

    response = client.post(
        "/interop/abdm/consent-callbacks",
        json={
            "patient_id": patient.id,
            "local_consent_id": consent.id,
            "abdm_request_id": "request-456",
            "status": "DENIED",
        },
        headers=_auth_headers(admin.username),
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Interoperability resource is outside the user's facility"


def test_patient_cannot_record_abdm_consent_callback(client, db_session):
    patient = _create_user(db_session, "interop_abdm_callback_forbidden_patient", "patient")

    response = client.post(
        "/interop/abdm/consent-callbacks",
        json={
            "patient_id": patient.id,
            "abdm_request_id": "request-789",
            "status": "GRANTED",
        },
        headers=_auth_headers(patient.username),
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Admin privileges required"
