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


def _create_encounter(
    db_session,
    patient_id: int,
    doctor_id: int,
    *,
    facility_id: int | None = None,
) -> models.Encounter:
    department = models.Department(
        name=f"Billing Department {patient_id}-{doctor_id}",
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
        reason="Billing visit",
        status="open",
    )
    db_session.add(encounter)
    db_session.commit()
    db_session.refresh(encounter)
    return encounter


def _service_payload(name: str = "General Consultation", unit_price: float = 500) -> dict:
    return {
        "service_code": name.upper().replace(" ", "-"),
        "name": name,
        "service_type": "consultation",
        "unit_price": unit_price,
    }


def _create_service(client, billing_username: str, name: str = "General Consultation", unit_price: float = 500) -> dict:
    response = client.post(
        "/billing/services",
        headers=_auth_headers(billing_username),
        json=_service_payload(name, unit_price),
    )
    assert response.status_code == 200
    return response.json()


def _invoice_payload(patient_id: int, encounter_id: int, service_id: int) -> dict:
    return {
        "patient_id": patient_id,
        "encounter_id": encounter_id,
        "discount_amount": 50,
        "tax_amount": 25,
        "items": [
            {
                "service_id": service_id,
                "description": "General Consultation",
                "quantity": 2,
                "unit_price": 500,
            }
        ],
    }


def _create_invoice(client, billing_username: str, patient_id: int, encounter_id: int, service_id: int) -> dict:
    response = client.post(
        "/billing/invoices",
        headers=_auth_headers(billing_username),
        json=_invoice_payload(patient_id, encounter_id, service_id),
    )
    assert response.status_code == 200
    return response.json()


def _create_department(db_session, name: str, facility_id: int | None = None) -> models.Department:
    department = models.Department(
        name=name,
        facility_id=facility_id,
        department_type="OPD",
        status="active",
    )
    db_session.add(department)
    db_session.commit()
    db_session.refresh(department)
    return department


def test_patient_cannot_create_billable_service(client, db_session):
    patient = _create_user(db_session, "billing_patient", "patient")
    patient_username = patient.username

    response = client.post(
        "/billing/services",
        headers=_auth_headers(patient_username),
        json=_service_payload(),
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Billing or admin privileges required"


def test_billing_staff_creates_service_and_invoice_totals(client, db_session):
    billing_user = _create_user(db_session, "billing_staff_invoice", "billing")
    doctor = _create_user(db_session, "billing_invoice_doctor", "doctor")
    patient = _create_user(db_session, "billing_invoice_patient", "patient")
    billing_username = billing_user.username
    patient_id = patient.id
    doctor_id = doctor.id
    encounter = _create_encounter(db_session, patient_id, doctor_id)
    encounter_id = encounter.id
    service = _create_service(client, billing_username)

    response = client.post(
        "/billing/invoices",
        headers=_auth_headers(billing_username),
        json=_invoice_payload(patient_id, encounter_id, service["id"]),
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["patient_id"] == patient_id
    assert payload["status"] == "issued"
    assert payload["subtotal"] == 1000
    assert payload["discount_amount"] == 50
    assert payload["tax_amount"] == 25
    assert payload["total_amount"] == 975
    assert payload["balance_amount"] == 975
    assert payload["items"][0]["line_total"] == 1000


def test_billing_service_persists_department_facility_and_lists_same_facility(client, db_session):
    primary_facility = _create_facility(db_session, "Billing Service Primary")
    other_facility = _create_facility(db_session, "Billing Service Other")
    primary_id = primary_facility.id
    other_id = other_facility.id
    billing_user = _create_user(
        db_session,
        "billing_service_facility_staff",
        "billing",
        facility_id=primary_id,
    )
    other_billing_user = _create_user(
        db_session,
        "billing_service_other_staff",
        "billing",
        facility_id=other_id,
    )
    primary_department = _create_department(db_session, "Billing Service Primary OPD", primary_id)
    other_department = _create_department(db_session, "Billing Service Other OPD", other_id)
    billing_username = billing_user.username
    other_billing_username = other_billing_user.username
    primary_department_id = primary_department.id
    other_department_id = other_department.id

    primary_response = client.post(
        "/billing/services",
        headers=_auth_headers(billing_username),
        json={**_service_payload("Primary Consultation"), "department_id": primary_department_id},
    )
    other_response = client.post(
        "/billing/services",
        headers=_auth_headers(other_billing_username),
        json={**_service_payload("Other Consultation"), "department_id": other_department_id},
    )
    list_response = client.get(
        "/billing/services",
        headers=_auth_headers(billing_username),
    )

    assert primary_response.status_code == 200
    assert primary_response.json()["facility_id"] == primary_id
    assert other_response.status_code == 200
    service_ids = {service["id"] for service in list_response.json()}
    assert primary_response.json()["id"] in service_ids
    assert other_response.json()["id"] not in service_ids


def test_billing_staff_cannot_create_invoice_for_patient_in_another_facility(client, db_session):
    primary_facility = _create_facility(db_session, "Billing Invoice Primary")
    other_facility = _create_facility(db_session, "Billing Invoice Other")
    billing_user = _create_user(
        db_session,
        "billing_cross_facility_staff",
        "billing",
        facility_id=primary_facility.id,
    )
    doctor = _create_user(db_session, "billing_cross_facility_doctor", "doctor", facility_id=other_facility.id)
    patient = _create_user(db_session, "billing_cross_facility_patient", "patient", facility_id=other_facility.id)
    encounter = _create_encounter(
        db_session,
        patient.id,
        doctor.id,
        facility_id=other_facility.id,
    )
    billing_username = billing_user.username
    patient_id = patient.id
    encounter_id = encounter.id
    service = _create_service(client, billing_username, "Cross Facility Consultation")

    response = client.post(
        "/billing/invoices",
        headers=_auth_headers(billing_username),
        json=_invoice_payload(patient_id, encounter_id, service["id"]),
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Billing resources must belong to the same facility"


def test_invoice_persists_facility_and_invoice_list_is_facility_scoped(client, db_session):
    primary_facility = _create_facility(db_session, "Billing List Primary")
    other_facility = _create_facility(db_session, "Billing List Other")
    primary_id = primary_facility.id
    other_id = other_facility.id
    billing_user = _create_user(db_session, "billing_list_staff", "billing", facility_id=primary_id)
    other_billing_user = _create_user(db_session, "billing_list_other_staff", "billing", facility_id=other_id)
    doctor = _create_user(db_session, "billing_list_doctor", "doctor", facility_id=primary_id)
    other_doctor = _create_user(db_session, "billing_list_other_doctor", "doctor", facility_id=other_id)
    patient = _create_user(db_session, "billing_list_patient", "patient", facility_id=primary_id)
    other_patient = _create_user(db_session, "billing_list_other_patient", "patient", facility_id=other_id)
    encounter = _create_encounter(db_session, patient.id, doctor.id, facility_id=primary_id)
    other_encounter = _create_encounter(db_session, other_patient.id, other_doctor.id, facility_id=other_id)
    billing_username = billing_user.username
    other_billing_username = other_billing_user.username
    patient_id = patient.id
    other_patient_id = other_patient.id
    encounter_id = encounter.id
    other_encounter_id = other_encounter.id
    service = _create_service(client, billing_username, "Facility Scoped Consultation")
    other_service = _create_service(client, other_billing_username, "Other Facility Consultation")

    invoice = _create_invoice(client, billing_username, patient_id, encounter_id, service["id"])
    other_invoice = _create_invoice(
        client,
        other_billing_username,
        other_patient_id,
        other_encounter_id,
        other_service["id"],
    )
    response = client.get("/billing/admin/invoices", headers=_auth_headers(billing_username))

    assert invoice["facility_id"] == primary_id
    assert other_invoice["facility_id"] == other_id
    assert response.status_code == 200
    invoice_ids = [item["id"] for item in response.json()]
    assert invoice["id"] in invoice_ids
    assert other_invoice["id"] not in invoice_ids


def test_invoice_admission_must_match_invoice_encounter(client, db_session):
    billing_user = _create_user(db_session, "billing_context_staff", "billing")
    doctor = _create_user(db_session, "billing_context_doctor", "doctor")
    patient = _create_user(db_session, "billing_context_patient", "patient")
    billing_username = billing_user.username
    patient_id = patient.id
    doctor_id = doctor.id
    invoice_encounter = _create_encounter(db_session, patient_id, doctor_id)
    admission_encounter = models.Encounter(
        patient_id=patient_id,
        doctor_id=doctor_id,
        department_id=invoice_encounter.department_id,
        encounter_type="IPD",
        reason="Billing admission episode",
        status="open",
    )
    db_session.add(admission_encounter)
    db_session.flush()
    admission = models.Admission(
        encounter_id=admission_encounter.id,
        patient_id=patient_id,
        doctor_id=doctor_id,
        department_id=admission_encounter.department_id,
        reason="Billing context admission",
        status="active",
    )
    db_session.add(admission)
    db_session.commit()
    db_session.refresh(admission)
    invoice_encounter_id = invoice_encounter.id
    admission_id = admission.id
    service = _create_service(client, billing_username)

    response = client.post(
        "/billing/invoices",
        headers=_auth_headers(billing_username),
        json={
            **_invoice_payload(patient_id, invoice_encounter_id, service["id"]),
            "admission_id": admission_id,
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Admission encounter must match invoice encounter"


def test_patient_sees_only_own_invoices(client, db_session):
    billing_user = _create_user(db_session, "billing_scope_staff", "billing")
    doctor = _create_user(db_session, "billing_scope_doctor", "doctor")
    patient = _create_user(db_session, "billing_scope_patient", "patient")
    other_patient = _create_user(db_session, "billing_scope_other", "patient")
    billing_username = billing_user.username
    patient_username = patient.username
    patient_id = patient.id
    other_patient_id = other_patient.id
    doctor_id = doctor.id
    service = _create_service(client, billing_username)
    encounter = _create_encounter(db_session, patient_id, doctor_id)
    other_encounter = _create_encounter(db_session, other_patient_id, doctor_id)
    encounter_id = encounter.id
    other_encounter_id = other_encounter.id
    own_invoice = _create_invoice(client, billing_username, patient_id, encounter_id, service["id"])
    _create_invoice(client, billing_username, other_patient_id, other_encounter_id, service["id"])

    response = client.get("/billing/patient/invoices", headers=_auth_headers(patient_username))

    assert response.status_code == 200
    assert [item["id"] for item in response.json()] == [own_invoice["id"]]


def test_cashier_records_payment_and_invoice_balances(client, db_session):
    billing_user = _create_user(db_session, "billing_payment_staff", "billing")
    doctor = _create_user(db_session, "billing_payment_doctor", "doctor")
    patient = _create_user(db_session, "billing_payment_patient", "patient")
    billing_username = billing_user.username
    patient_id = patient.id
    doctor_id = doctor.id
    encounter = _create_encounter(db_session, patient_id, doctor_id)
    encounter_id = encounter.id
    service = _create_service(client, billing_username)
    invoice = _create_invoice(client, billing_username, patient_id, encounter_id, service["id"])

    partial = client.post(
        f"/billing/invoices/{invoice['id']}/payments",
        headers=_auth_headers(billing_username),
        json={
            "amount": 500,
            "payment_method": "cash",
            "reference_id": "SYNTH-RECEIPT-1",
        },
    )
    final = client.post(
        f"/billing/invoices/{invoice['id']}/payments",
        headers=_auth_headers(billing_username),
        json={
            "amount": 475,
            "payment_method": "upi",
            "reference_id": "SYNTH-RECEIPT-2",
        },
    )

    assert partial.status_code == 200
    assert partial.json()["invoice"]["status"] == "partially_paid"
    assert partial.json()["invoice"]["balance_amount"] == 475
    assert final.status_code == 200
    assert final.json()["invoice"]["status"] == "paid"
    assert final.json()["invoice"]["paid_amount"] == 975
    assert final.json()["invoice"]["balance_amount"] == 0


def test_billing_staff_cannot_record_payment_for_other_facility_invoice(client, db_session):
    primary_facility = _create_facility(db_session, "Billing Payment Primary")
    other_facility = _create_facility(db_session, "Billing Payment Other")
    billing_user = _create_user(db_session, "billing_payment_primary_staff", "billing", facility_id=primary_facility.id)
    other_billing_user = _create_user(db_session, "billing_payment_other_staff", "billing", facility_id=other_facility.id)
    doctor = _create_user(db_session, "billing_payment_other_doctor", "doctor", facility_id=other_facility.id)
    patient = _create_user(db_session, "billing_payment_other_patient", "patient", facility_id=other_facility.id)
    encounter = _create_encounter(db_session, patient.id, doctor.id, facility_id=other_facility.id)
    billing_username = billing_user.username
    other_billing_username = other_billing_user.username
    patient_id = patient.id
    encounter_id = encounter.id
    service = _create_service(client, other_billing_username, "Other Payment Consultation")
    invoice = _create_invoice(client, other_billing_username, patient_id, encounter_id, service["id"])

    response = client.post(
        f"/billing/invoices/{invoice['id']}/payments",
        headers=_auth_headers(billing_username),
        json={"amount": 100, "payment_method": "cash"},
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Billing resource is outside the user's facility"


def test_payment_rejects_overpayment(client, db_session):
    billing_user = _create_user(db_session, "billing_overpay_staff", "billing")
    doctor = _create_user(db_session, "billing_overpay_doctor", "doctor")
    patient = _create_user(db_session, "billing_overpay_patient", "patient")
    billing_username = billing_user.username
    patient_id = patient.id
    doctor_id = doctor.id
    encounter = _create_encounter(db_session, patient_id, doctor_id)
    encounter_id = encounter.id
    service = _create_service(client, billing_username)
    invoice = _create_invoice(client, billing_username, patient_id, encounter_id, service["id"])

    response = client.post(
        f"/billing/invoices/{invoice['id']}/payments",
        headers=_auth_headers(billing_username),
        json={
            "amount": 1000,
            "payment_method": "cash",
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Payment amount exceeds invoice balance"


def test_admin_billing_metrics(client, db_session):
    admin = _create_user(db_session, "billing_metrics_admin", "admin")
    billing_user = _create_user(db_session, "billing_metrics_staff", "billing")
    doctor = _create_user(db_session, "billing_metrics_doctor", "doctor")
    patient = _create_user(db_session, "billing_metrics_patient", "patient")
    admin_username = admin.username
    billing_username = billing_user.username
    patient_id = patient.id
    doctor_id = doctor.id
    encounter = _create_encounter(db_session, patient_id, doctor_id)
    encounter_id = encounter.id
    service = _create_service(client, billing_username)
    invoice = _create_invoice(client, billing_username, patient_id, encounter_id, service["id"])
    client.post(
        f"/billing/invoices/{invoice['id']}/payments",
        headers=_auth_headers(billing_username),
        json={
            "amount": 500,
            "payment_method": "cash",
        },
    )

    response = client.get("/billing/admin/metrics", headers=_auth_headers(admin_username))

    assert response.status_code == 200
    payload = response.json()
    assert payload["total_services"] == 1
    assert payload["total_invoices"] == 1
    assert payload["partially_paid_invoices"] == 1
    assert payload["total_billed"] == 975
    assert payload["total_collected"] == 500
    assert payload["outstanding_balance"] == 475


def test_billing_metrics_are_facility_scoped_for_billing_staff(client, db_session):
    primary_facility = _create_facility(db_session, "Billing Metrics Primary")
    other_facility = _create_facility(db_session, "Billing Metrics Other")
    primary_id = primary_facility.id
    other_id = other_facility.id
    billing_user = _create_user(db_session, "billing_metrics_primary_staff", "billing", facility_id=primary_id)
    other_billing_user = _create_user(db_session, "billing_metrics_other_staff", "billing", facility_id=other_id)
    doctor = _create_user(db_session, "billing_metrics_primary_doctor", "doctor", facility_id=primary_id)
    other_doctor = _create_user(db_session, "billing_metrics_other_doctor", "doctor", facility_id=other_id)
    patient = _create_user(db_session, "billing_metrics_primary_patient", "patient", facility_id=primary_id)
    other_patient = _create_user(db_session, "billing_metrics_other_patient", "patient", facility_id=other_id)
    encounter = _create_encounter(db_session, patient.id, doctor.id, facility_id=primary_id)
    other_encounter = _create_encounter(db_session, other_patient.id, other_doctor.id, facility_id=other_id)
    billing_username = billing_user.username
    other_billing_username = other_billing_user.username
    patient_id = patient.id
    other_patient_id = other_patient.id
    encounter_id = encounter.id
    other_encounter_id = other_encounter.id
    service = _create_service(client, billing_username, "Primary Metrics Consultation")
    other_service = _create_service(client, other_billing_username, "Other Metrics Consultation")
    invoice = _create_invoice(client, billing_username, patient_id, encounter_id, service["id"])
    other_invoice = _create_invoice(
        client,
        other_billing_username,
        other_patient_id,
        other_encounter_id,
        other_service["id"],
    )
    client.post(
        f"/billing/invoices/{invoice['id']}/payments",
        headers=_auth_headers(billing_username),
        json={"amount": 500, "payment_method": "cash"},
    )
    client.post(
        f"/billing/invoices/{other_invoice['id']}/payments",
        headers=_auth_headers(other_billing_username),
        json={"amount": 975, "payment_method": "cash"},
    )

    response = client.get("/billing/admin/metrics", headers=_auth_headers(billing_username))

    assert response.status_code == 200
    payload = response.json()
    assert payload["total_services"] == 1
    assert payload["total_invoices"] == 1
    assert payload["partially_paid_invoices"] == 1
    assert payload["paid_invoices"] == 0
    assert payload["total_billed"] == 975
    assert payload["total_collected"] == 500
    assert payload["outstanding_balance"] == 475
