from backend import audit, auth, models


def _auth_headers(db_session, username: str, role: str) -> dict[str, str]:
    user = models.User(
        username=username,
        email=f"{username}@example.com",
        hashed_password=auth.get_password_hash("StrongPassword123!"),
        role=role,
    )
    db_session.add(user)
    db_session.commit()

    token = auth.create_access_token({"sub": username})
    return {"Authorization": f"Bearer {token}"}


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
        hashed_password=auth.get_password_hash("StrongPassword123!"),
        role=role,
        facility_id=facility_id,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def _headers_for(username: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {auth.create_access_token({'sub': username})}"}


def test_admin_routes_reject_admin_prefixed_patient_username(client, db_session):
    headers = _auth_headers(db_session, "admin_mallory", "patient")

    response = client.get("/admin/users", headers=headers)

    assert response.status_code == 403
    assert response.json()["detail"] == "Admin privileges required"


def test_admin_routes_allow_admin_role_without_special_username(client, db_session):
    headers = _auth_headers(db_session, "clinic_manager", "admin")

    response = client.get("/admin/users", headers=headers)

    assert response.status_code == 200
    assert response.json()[0]["username"] == "clinic_manager"
    assert response.json()[0]["role"] == "admin"


def test_admin_can_fetch_patient_profile_by_id_without_user_directory(client, db_session):
    headers = _auth_headers(db_session, "patient_lookup_admin", "admin")
    patient = models.User(
        username="lookup_patient",
        email="lookup_patient@example.com",
        full_name="Lookup Patient",
        hashed_password=auth.get_password_hash("StrongPassword123!"),
        role="patient",
        dob="1991-02-03",
        gender="female",
        blood_type="B+",
    )
    db_session.add(patient)
    db_session.commit()
    db_session.refresh(patient)

    response = client.get(f"/admin/patients/{patient.id}", headers=headers)

    assert response.status_code == 200
    payload = response.json()
    assert payload["id"] == patient.id
    assert payload["username"] == "lookup_patient"
    assert payload["full_name"] == "Lookup Patient"
    assert payload["role"] == "patient"
    assert payload["dob"] == "1991-02-03"
    assert payload["gender"] == "female"
    assert payload["blood_type"] == "B+"
    assert "hashed_password" not in payload


def test_facility_admin_user_list_is_scoped_to_own_facility(client, db_session):
    primary_facility = _create_facility(db_session, "Admin Directory Primary")
    other_facility = _create_facility(db_session, "Admin Directory Other")
    admin = _create_user(db_session, "facility_directory_admin", "admin", facility_id=primary_facility.id)
    local_patient = _create_user(db_session, "facility_directory_patient", "patient", facility_id=primary_facility.id)
    other_patient = _create_user(db_session, "facility_directory_other", "patient", facility_id=other_facility.id)
    _create_user(db_session, "facility_directory_unassigned", "patient")
    admin_username = admin.username
    local_patient_username = local_patient.username
    other_patient_username = other_patient.username

    response = client.get("/admin/users", headers=_headers_for(admin_username))

    assert response.status_code == 200
    usernames = {user["username"] for user in response.json()}
    assert admin_username in usernames
    assert local_patient_username in usernames
    assert other_patient_username not in usernames
    assert "facility_directory_unassigned" not in usernames


def test_facility_admin_patient_profile_rejects_other_facility_patient(client, db_session):
    primary_facility = _create_facility(db_session, "Admin Profile Primary")
    other_facility = _create_facility(db_session, "Admin Profile Other")
    admin = _create_user(db_session, "facility_profile_admin", "admin", facility_id=primary_facility.id)
    patient = _create_user(db_session, "facility_profile_other_patient", "patient", facility_id=other_facility.id)

    response = client.get(f"/admin/patients/{patient.id}", headers=_headers_for(admin.username))

    assert response.status_code == 403
    assert response.json()["detail"] == "Admin resource is outside the user's facility"


def test_facility_admin_cannot_update_role_for_other_facility_user(client, db_session):
    primary_facility = _create_facility(db_session, "Admin Role Primary")
    other_facility = _create_facility(db_session, "Admin Role Other")
    admin = _create_user(db_session, "facility_role_admin", "admin", facility_id=primary_facility.id)
    user = _create_user(db_session, "facility_role_other_user", "patient", facility_id=other_facility.id)

    response = client.put(
        f"/admin/users/{user.id}/role?role=nurse",
        headers=_headers_for(admin.username),
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Admin resource is outside the user's facility"
    assert db_session.get(models.User, user.id).role == "patient"


def test_facility_admin_stats_are_scoped_to_own_facility(client, db_session):
    primary_facility = _create_facility(db_session, "Admin Stats Primary")
    other_facility = _create_facility(db_session, "Admin Stats Other")
    admin = _create_user(db_session, "facility_stats_admin", "admin", facility_id=primary_facility.id)
    local_patient = _create_user(db_session, "facility_stats_patient", "patient", facility_id=primary_facility.id)
    other_patient = _create_user(db_session, "facility_stats_other", "patient", facility_id=other_facility.id)
    db_session.add(models.HealthRecord(
        user_id=local_patient.id,
        record_type="diabetes",
        data="{}",
        prediction="Low risk",
    ))
    db_session.add(models.HealthRecord(
        user_id=other_patient.id,
        record_type="diabetes",
        data="{}",
        prediction="High risk",
    ))
    db_session.add(models.ChatLog(user_id=local_patient.id, role="user", content="Local synthetic message"))
    db_session.add(models.ChatLog(user_id=other_patient.id, role="user", content="Other synthetic message"))
    db_session.commit()

    response = client.get("/admin/stats", headers=_headers_for(admin.username))

    assert response.status_code == 200
    payload = response.json()
    assert payload["total_users"] == 2
    assert payload["total_predictions"] == 1
    assert payload["total_messages"] == 1


def test_facility_admin_audit_logs_are_scoped_to_own_facility(client, db_session):
    primary_facility = _create_facility(db_session, "Admin Audit Primary")
    other_facility = _create_facility(db_session, "Admin Audit Other")
    admin = _create_user(db_session, "facility_audit_admin", "admin", facility_id=primary_facility.id)
    local_patient = _create_user(db_session, "facility_audit_patient", "patient", facility_id=primary_facility.id)
    other_admin = _create_user(db_session, "facility_audit_other_admin", "admin", facility_id=other_facility.id)
    other_patient = _create_user(db_session, "facility_audit_other_patient", "patient", facility_id=other_facility.id)
    audit.record_audit_event(
        db_session,
        actor_user_id=admin.id,
        target_user_id=local_patient.id,
        action="VIEW_LOCAL_PATIENT",
        details={"resource_type": "patient"},
    )
    audit.record_audit_event(
        db_session,
        actor_user_id=other_admin.id,
        target_user_id=other_patient.id,
        action="VIEW_OTHER_PATIENT",
        details={"resource_type": "patient"},
    )
    audit.record_audit_event(
        db_session,
        actor_user_id=None,
        target_user_id=None,
        action="SYSTEM_WIDE_EVENT",
        details={"resource_type": "system"},
    )
    primary_facility_id = primary_facility.id

    response = client.get("/admin/audit-logs", headers=_headers_for(admin.username))

    assert response.status_code == 200
    payload = response.json()
    assert [entry["action"] for entry in payload] == ["VIEW_LOCAL_PATIENT"]
    assert payload[0]["facility_id"] == primary_facility_id


def test_facility_admin_audit_log_filter_rejects_other_facility_target(client, db_session):
    primary_facility = _create_facility(db_session, "Admin Audit Filter Primary")
    other_facility = _create_facility(db_session, "Admin Audit Filter Other")
    admin = _create_user(db_session, "facility_audit_filter_admin", "admin", facility_id=primary_facility.id)
    other_admin = _create_user(db_session, "facility_audit_filter_other_admin", "admin", facility_id=other_facility.id)
    other_patient = _create_user(db_session, "facility_audit_filter_patient", "patient", facility_id=other_facility.id)
    audit.record_audit_event(
        db_session,
        actor_user_id=other_admin.id,
        target_user_id=other_patient.id,
        action="VIEW_OTHER_FILTERED_PATIENT",
        details={"resource_type": "patient"},
    )

    response = client.get(
        f"/admin/audit-logs?target_user_id={other_patient.id}",
        headers=_headers_for(admin.username),
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Admin resource is outside the user's facility"


def test_global_admin_delete_user_audit_is_visible_to_target_facility_admin(client, db_session):
    facility = _create_facility(db_session, "Admin Delete Audit Facility")
    global_admin = _create_user(db_session, "delete_audit_global_admin", "admin")
    facility_admin = _create_user(db_session, "delete_audit_facility_admin", "admin", facility_id=facility.id)
    patient = _create_user(db_session, "delete_audit_patient", "patient", facility_id=facility.id)
    global_admin_username = global_admin.username
    facility_admin_username = facility_admin.username
    patient_id = patient.id
    facility_id = facility.id

    delete_response = client.delete(
        f"/admin/users/{patient_id}",
        headers=_headers_for(global_admin_username),
    )
    audit_response = client.get(
        "/admin/audit-logs?action=DELETE_USER",
        headers=_headers_for(facility_admin_username),
    )

    assert delete_response.status_code == 200
    assert audit_response.status_code == 200
    payload = audit_response.json()
    assert [entry["target_user_id"] for entry in payload] == [patient_id]
    assert payload[0]["facility_id"] == facility_id


def test_admin_patient_list_returns_patients_only(client, db_session):
    headers = _auth_headers(db_session, "patient_list_admin", "admin")
    patient = models.User(
        username="patient_list_patient",
        email="patient_list_patient@example.com",
        full_name="Patient List Patient",
        hashed_password=auth.get_password_hash("StrongPassword123!"),
        role="patient",
    )
    doctor = models.User(
        username="patient_list_doctor",
        email="patient_list_doctor@example.com",
        full_name="Patient List Doctor",
        hashed_password=auth.get_password_hash("StrongPassword123!"),
        role="doctor",
    )
    db_session.add_all([patient, doctor])
    db_session.commit()

    response = client.get("/admin/patients", headers=headers)

    assert response.status_code == 200
    payload = response.json()
    assert [item["username"] for item in payload] == ["patient_list_patient"]
    assert payload[0]["role"] == "patient"


def test_admin_patient_lookup_rejects_staff_accounts(client, db_session):
    headers = _auth_headers(db_session, "staff_lookup_admin", "admin")
    doctor = models.User(
        username="lookup_doctor",
        email="lookup_doctor@example.com",
        full_name="Lookup Doctor",
        hashed_password=auth.get_password_hash("StrongPassword123!"),
        role="doctor",
    )
    db_session.add(doctor)
    db_session.commit()
    db_session.refresh(doctor)

    response = client.get(f"/admin/patients/{doctor.id}", headers=headers)

    assert response.status_code == 404
    assert response.json()["detail"] == "Patient not found"


def test_admin_can_assign_pharmacist_role(client, db_session):
    headers = _auth_headers(db_session, "role_admin", "admin")
    pharmacist = models.User(
        username="role_pharmacist",
        email="role_pharmacist@example.com",
        hashed_password=auth.get_password_hash("StrongPassword123!"),
        role="patient",
    )
    db_session.add(pharmacist)
    db_session.commit()
    db_session.refresh(pharmacist)
    pharmacist_id = pharmacist.id

    response = client.put(
        f"/admin/users/{pharmacist_id}/role?role=pharmacist",
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json()["message"] == "User role updated to pharmacist"
    assert db_session.get(models.User, pharmacist_id).role == "pharmacist"


def test_admin_can_assign_billing_role(client, db_session):
    headers = _auth_headers(db_session, "billing_role_admin", "admin")
    billing_user = models.User(
        username="role_billing",
        email="role_billing@example.com",
        hashed_password=auth.get_password_hash("StrongPassword123!"),
        role="patient",
    )
    db_session.add(billing_user)
    db_session.commit()
    db_session.refresh(billing_user)
    billing_user_id = billing_user.id

    response = client.put(
        f"/admin/users/{billing_user_id}/role?role=billing",
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json()["message"] == "User role updated to billing"
    assert db_session.get(models.User, billing_user_id).role == "billing"


def test_admin_can_assign_nurse_role(client, db_session):
    headers = _auth_headers(db_session, "nurse_role_admin", "admin")
    nurse = models.User(
        username="role_nurse",
        email="role_nurse@example.com",
        hashed_password=auth.get_password_hash("StrongPassword123!"),
        role="patient",
    )
    db_session.add(nurse)
    db_session.commit()
    db_session.refresh(nurse)
    nurse_id = nurse.id

    response = client.put(
        f"/admin/users/{nurse_id}/role?role=nurse",
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json()["message"] == "User role updated to nurse"
    assert db_session.get(models.User, nurse_id).role == "nurse"


def test_admin_cannot_demote_own_account(client, db_session):
    admin = _create_user(db_session, "self_demote_admin", "admin")

    response = client.put(
        f"/admin/users/{admin.id}/role?role=patient",
        headers=_headers_for(admin.username),
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Cannot change your own admin role."
    assert db_session.get(models.User, admin.id).role == "admin"


def test_facility_admin_cannot_claim_unassigned_user(client, db_session):
    facility = _create_facility(db_session, "Admin Claim Facility")
    admin = _create_user(db_session, "facility_claim_admin", "admin", facility_id=facility.id)
    unassigned_user = _create_user(db_session, "facility_claim_unassigned", "patient")

    response = client.put(
        f"/admin/users/{unassigned_user.id}/facility?facility_id={facility.id}",
        headers=_headers_for(admin.username),
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Admin resource is outside the user's facility"
    assert db_session.get(models.User, unassigned_user.id).facility_id is None


def test_get_analytics_report_success(client, db_session):
    headers = _auth_headers(db_session, "analytics_admin", "admin")

    response = client.get("/admin/analytics/report", headers=headers)
    assert response.status_code == 200
    payload = response.json()
    assert "total_records_analyzed" in payload
    assert isinstance(payload["total_records_analyzed"], int)
    assert "pipeline_execution" in payload
    assert "status" in payload["pipeline_execution"]


def test_get_analytics_report_forbidden_for_patient(client, db_session):
    headers = _auth_headers(db_session, "analytics_patient", "patient")

    response = client.get("/admin/analytics/report", headers=headers)
    assert response.status_code == 403

