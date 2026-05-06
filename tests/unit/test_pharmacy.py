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
        name=f"Pharmacy Department {patient_id}-{doctor_id}",
        facility_id=facility_id,
        department_type="Pharmacy",
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
        reason="Medication review",
        status="open",
    )
    db_session.add(encounter)
    db_session.commit()
    db_session.refresh(encounter)
    return encounter


def _inventory_payload(name: str = "Paracetamol", quantity_on_hand: float = 100) -> dict:
    return {
        "medication_name": name,
        "strength": "500mg",
        "form": "tablet",
        "batch_number": "BATCH-001",
        "quantity_on_hand": quantity_on_hand,
        "reorder_level": 10,
    }


def _create_inventory(
    client,
    admin_username: str,
    name: str = "Paracetamol",
    quantity_on_hand: float = 100,
) -> dict:
    response = client.post(
        "/pharmacy/inventory",
        headers=_auth_headers(admin_username),
        json=_inventory_payload(name, quantity_on_hand),
    )
    assert response.status_code == 200
    return response.json()


def _prescription_payload(patient_id: int, doctor_id: int, encounter_id: int, inventory_id: int) -> dict:
    return {
        "patient_id": patient_id,
        "doctor_id": doctor_id,
        "encounter_id": encounter_id,
        "diagnosis_context": "Clinician-reviewed fever management",
        "items": [
            {
                "inventory_id": inventory_id,
                "medication_name": "Paracetamol",
                "dosage": "500mg",
                "frequency": "Twice daily",
                "duration": "3 days",
                "quantity_prescribed": 6,
                "instructions": "After food",
            }
        ],
    }


def _create_prescription(
    client,
    doctor_username: str,
    patient_id: int,
    doctor_id: int,
    encounter_id: int,
    inventory_id: int,
) -> dict:
    response = client.post(
        "/pharmacy/prescriptions",
        headers=_auth_headers(doctor_username),
        json=_prescription_payload(patient_id, doctor_id, encounter_id, inventory_id),
    )
    assert response.status_code == 200
    return response.json()


def test_patient_cannot_create_pharmacy_inventory(client, db_session):
    patient = _create_user(db_session, "pharmacy_patient", "patient")
    patient_username = patient.username

    response = client.post(
        "/pharmacy/inventory",
        headers=_auth_headers(patient_username),
        json=_inventory_payload(),
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Pharmacy or admin privileges required"


def test_admin_creates_and_lists_inventory(client, db_session):
    admin = _create_user(db_session, "pharmacy_admin", "admin")
    admin_username = admin.username

    item = _create_inventory(client, admin_username)
    response = client.get("/pharmacy/inventory", headers=_auth_headers(admin_username))

    assert response.status_code == 200
    assert response.json()[0]["id"] == item["id"]
    assert response.json()[0]["quantity_on_hand"] == 100


def test_pharmacist_can_create_inventory(client, db_session):
    pharmacist = _create_user(db_session, "pharmacy_inventory_staff", "pharmacist")
    pharmacist_username = pharmacist.username

    response = client.post(
        "/pharmacy/inventory",
        headers=_auth_headers(pharmacist_username),
        json=_inventory_payload("Amoxicillin"),
    )

    assert response.status_code == 200
    assert response.json()["medication_name"] == "Amoxicillin"


def test_pharmacist_inventory_persists_facility_and_lists_same_facility(client, db_session):
    primary_facility = _create_facility(db_session, "Pharmacy Inventory Primary")
    other_facility = _create_facility(db_session, "Pharmacy Inventory Other")
    primary_id = primary_facility.id
    other_id = other_facility.id
    pharmacist = _create_user(db_session, "pharmacy_facility_staff", "pharmacist", facility_id=primary_id)
    other_pharmacist = _create_user(
        db_session,
        "pharmacy_facility_other_staff",
        "pharmacist",
        facility_id=other_id,
    )
    pharmacist_username = pharmacist.username
    other_pharmacist_username = other_pharmacist.username

    own_item = _create_inventory(client, pharmacist_username, "Facility Paracetamol")
    other_item = _create_inventory(client, other_pharmacist_username, "Other Facility Paracetamol")
    response = client.get("/pharmacy/inventory", headers=_auth_headers(pharmacist_username))

    assert own_item["facility_id"] == primary_id
    assert other_item["facility_id"] == other_id
    assert response.status_code == 200
    inventory_ids = {item["id"] for item in response.json()}
    assert own_item["id"] in inventory_ids
    assert other_item["id"] not in inventory_ids


def test_doctor_creates_prescription_for_assigned_patient(client, db_session):
    admin = _create_user(db_session, "rx_admin", "admin")
    doctor = _create_user(db_session, "rx_doctor", "doctor")
    patient = _create_user(db_session, "rx_patient", "patient")
    admin_username = admin.username
    doctor_username = doctor.username
    doctor_id = doctor.id
    patient_id = patient.id
    encounter = _create_encounter(db_session, patient_id, doctor_id)
    encounter_id = encounter.id
    inventory = _create_inventory(client, admin_username)

    response = client.post(
        "/pharmacy/prescriptions",
        headers=_auth_headers(doctor_username),
        json=_prescription_payload(patient_id, doctor_id, encounter_id, inventory["id"]),
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["patient_id"] == patient_id
    assert payload["status"] == "active"
    assert payload["items"][0]["medication_name"] == "Paracetamol"
    event = db_session.query(models.CareEvent).filter_by(event_type="PRESCRIPTION_CREATED").one()
    assert event.patient_id == patient_id


def test_doctor_cannot_prescribe_inventory_from_another_facility(client, db_session):
    primary_facility = _create_facility(db_session, "Pharmacy Prescription Primary")
    other_facility = _create_facility(db_session, "Pharmacy Prescription Other")
    primary_id = primary_facility.id
    other_id = other_facility.id
    doctor = _create_user(db_session, "rx_cross_facility_doctor", "doctor", facility_id=primary_id)
    patient = _create_user(db_session, "rx_cross_facility_patient", "patient", facility_id=primary_id)
    pharmacist = _create_user(db_session, "rx_cross_facility_pharmacist", "pharmacist", facility_id=other_id)
    doctor_username = doctor.username
    pharmacist_username = pharmacist.username
    doctor_id = doctor.id
    patient_id = patient.id
    encounter = _create_encounter(db_session, patient_id, doctor_id, facility_id=primary_id)
    encounter_id = encounter.id
    inventory = _create_inventory(client, pharmacist_username, "Other Facility Amoxicillin")

    response = client.post(
        "/pharmacy/prescriptions",
        headers=_auth_headers(doctor_username),
        json=_prescription_payload(patient_id, doctor_id, encounter_id, inventory["id"]),
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Pharmacy resources must belong to the same facility"


def test_prescription_persists_facility_and_care_event_facility(client, db_session):
    facility = _create_facility(db_session, "Pharmacy Prescription Facility")
    facility_id = facility.id
    pharmacist = _create_user(db_session, "rx_facility_pharmacist", "pharmacist", facility_id=facility_id)
    doctor = _create_user(db_session, "rx_facility_doctor", "doctor", facility_id=facility_id)
    patient = _create_user(db_session, "rx_facility_patient", "patient", facility_id=facility_id)
    pharmacist_username = pharmacist.username
    doctor_username = doctor.username
    doctor_id = doctor.id
    patient_id = patient.id
    encounter = _create_encounter(db_session, patient_id, doctor_id, facility_id=facility_id)
    encounter_id = encounter.id
    inventory = _create_inventory(client, pharmacist_username, "Facility Cefixime")

    response = client.post(
        "/pharmacy/prescriptions",
        headers=_auth_headers(doctor_username),
        json=_prescription_payload(patient_id, doctor_id, encounter_id, inventory["id"]),
    )

    assert response.status_code == 200
    assert response.json()["facility_id"] == facility_id
    event = db_session.query(models.CareEvent).filter_by(event_type="PRESCRIPTION_CREATED").one()
    assert event.facility_id == facility_id


def test_prescription_encounter_must_match_prescribing_doctor(client, db_session):
    admin = _create_user(db_session, "rx_context_admin", "admin")
    encounter_doctor = _create_user(db_session, "rx_context_encounter_doctor", "doctor")
    prescribing_doctor = _create_user(db_session, "rx_context_prescribing_doctor", "doctor")
    patient = _create_user(db_session, "rx_context_patient", "patient")
    admin_username = admin.username
    prescribing_username = prescribing_doctor.username
    patient_id = patient.id
    prescribing_doctor_id = prescribing_doctor.id
    encounter = _create_encounter(db_session, patient_id, encounter_doctor.id)
    encounter_id = encounter.id
    _create_encounter(db_session, patient_id, prescribing_doctor_id)
    inventory = _create_inventory(client, admin_username)

    response = client.post(
        "/pharmacy/prescriptions",
        headers=_auth_headers(prescribing_username),
        json=_prescription_payload(patient_id, prescribing_doctor_id, encounter_id, inventory["id"]),
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Encounter doctor must match prescription doctor"


def test_patient_sees_only_own_prescriptions(client, db_session):
    admin = _create_user(db_session, "rx_scope_admin", "admin")
    doctor = _create_user(db_session, "rx_scope_doctor", "doctor")
    patient = _create_user(db_session, "rx_scope_patient", "patient")
    other_patient = _create_user(db_session, "rx_scope_other", "patient")
    admin_username = admin.username
    doctor_username = doctor.username
    doctor_id = doctor.id
    patient_id = patient.id
    other_patient_id = other_patient.id
    patient_username = patient.username
    inventory = _create_inventory(client, admin_username)
    encounter = _create_encounter(db_session, patient_id, doctor_id)
    other_encounter = _create_encounter(db_session, other_patient_id, doctor_id)
    encounter_id = encounter.id
    other_encounter_id = other_encounter.id
    own_rx = _create_prescription(client, doctor_username, patient_id, doctor_id, encounter_id, inventory["id"])
    _create_prescription(client, doctor_username, other_patient_id, doctor_id, other_encounter_id, inventory["id"])

    response = client.get("/pharmacy/patient/prescriptions", headers=_auth_headers(patient_username))

    assert response.status_code == 200
    assert [item["id"] for item in response.json()] == [own_rx["id"]]


def test_assigned_doctor_can_view_patient_prescriptions(client, db_session):
    admin = _create_user(db_session, "rx_view_admin", "admin")
    doctor = _create_user(db_session, "rx_view_doctor", "doctor")
    patient = _create_user(db_session, "rx_view_patient", "patient")
    admin_username = admin.username
    doctor_username = doctor.username
    doctor_id = doctor.id
    patient_id = patient.id
    encounter = _create_encounter(db_session, patient_id, doctor_id)
    encounter_id = encounter.id
    inventory = _create_inventory(client, admin_username)
    prescription = _create_prescription(client, doctor_username, patient_id, doctor_id, encounter_id, inventory["id"])

    response = client.get(
        f"/pharmacy/doctor/patients/{patient_id}/prescriptions",
        headers=_auth_headers(doctor_username),
    )

    assert response.status_code == 200
    assert response.json()["patient_id"] == patient_id
    assert [item["id"] for item in response.json()["prescriptions"]] == [prescription["id"]]
    assert "clinician" in response.json()["clinical_safety_note"].lower()


def test_unassigned_doctor_cannot_view_patient_prescriptions(client, db_session):
    admin = _create_user(db_session, "rx_private_admin", "admin")
    assigned_doctor = _create_user(db_session, "rx_private_assigned", "doctor")
    other_doctor = _create_user(db_session, "rx_private_other", "doctor")
    patient = _create_user(db_session, "rx_private_patient", "patient")
    admin_username = admin.username
    assigned_doctor_username = assigned_doctor.username
    other_doctor_username = other_doctor.username
    assigned_doctor_id = assigned_doctor.id
    patient_id = patient.id
    encounter = _create_encounter(db_session, patient_id, assigned_doctor_id)
    encounter_id = encounter.id
    inventory = _create_inventory(client, admin_username)
    _create_prescription(
        client,
        assigned_doctor_username,
        patient_id,
        assigned_doctor_id,
        encounter_id,
        inventory["id"],
    )

    response = client.get(
        f"/pharmacy/doctor/patients/{patient_id}/prescriptions",
        headers=_auth_headers(other_doctor_username),
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Doctor is not assigned to this patient"


def test_facility_admin_doctor_prescriptions_route_rejects_other_facility_patient(client, db_session):
    primary_facility = _create_facility(db_session, "Pharmacy Doctor Admin Primary")
    other_facility = _create_facility(db_session, "Pharmacy Doctor Admin Other")
    admin = _create_user(db_session, "rx_doctor_route_facility_admin", "admin", facility_id=primary_facility.id)
    doctor = _create_user(db_session, "rx_doctor_route_other_doctor", "doctor", facility_id=other_facility.id)
    patient = _create_user(db_session, "rx_doctor_route_other_patient", "patient", facility_id=other_facility.id)
    db_session.add(models.Prescription(
        facility_id=other_facility.id,
        patient_id=patient.id,
        doctor_id=doctor.id,
        diagnosis_context="Synthetic diagnosis context.",
        status="active",
    ))
    db_session.commit()

    response = client.get(
        f"/pharmacy/doctor/patients/{patient.id}/prescriptions",
        headers=_auth_headers(admin.username),
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Pharmacy resource is outside the user's facility"


def test_pharmacist_dispenses_prescription_and_inventory_decrements(client, db_session):
    admin = _create_user(db_session, "dispense_admin", "admin")
    pharmacist = _create_user(db_session, "dispense_pharmacist", "pharmacist")
    doctor = _create_user(db_session, "dispense_doctor", "doctor")
    patient = _create_user(db_session, "dispense_patient", "patient")
    admin_username = admin.username
    pharmacist_username = pharmacist.username
    doctor_username = doctor.username
    doctor_id = doctor.id
    patient_id = patient.id
    encounter = _create_encounter(db_session, patient_id, doctor_id)
    encounter_id = encounter.id
    inventory = _create_inventory(client, admin_username)
    prescription = _create_prescription(client, doctor_username, patient_id, doctor_id, encounter_id, inventory["id"])

    response = client.post(
        f"/pharmacy/prescriptions/{prescription['id']}/dispense",
        headers=_auth_headers(pharmacist_username),
        json={
            "items": [
                {
                    "prescription_item_id": prescription["items"][0]["id"],
                    "quantity_dispensed": 6,
                }
            ]
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "dispensed"
    refreshed_inventory = db_session.get(models.MedicationInventory, inventory["id"])
    assert refreshed_inventory.quantity_on_hand == 94
    event = db_session.query(models.CareEvent).filter_by(event_type="PRESCRIPTION_DISPENSED").one()
    assert event.patient_id == patient_id


def test_pharmacist_cannot_dispense_other_facility_prescription(client, db_session):
    primary_facility = _create_facility(db_session, "Pharmacy Dispense Primary")
    other_facility = _create_facility(db_session, "Pharmacy Dispense Other")
    primary_id = primary_facility.id
    other_id = other_facility.id
    pharmacist = _create_user(db_session, "dispense_primary_pharmacist", "pharmacist", facility_id=primary_id)
    other_pharmacist = _create_user(db_session, "dispense_other_pharmacist", "pharmacist", facility_id=other_id)
    doctor = _create_user(db_session, "dispense_other_doctor", "doctor", facility_id=other_id)
    patient = _create_user(db_session, "dispense_other_patient", "patient", facility_id=other_id)
    pharmacist_username = pharmacist.username
    other_pharmacist_username = other_pharmacist.username
    doctor_username = doctor.username
    doctor_id = doctor.id
    patient_id = patient.id
    encounter = _create_encounter(db_session, patient_id, doctor_id, facility_id=other_id)
    encounter_id = encounter.id
    inventory = _create_inventory(client, other_pharmacist_username, "Other Facility Azithromycin")
    prescription = _create_prescription(
        client,
        doctor_username,
        patient_id,
        doctor_id,
        encounter_id,
        inventory["id"],
    )

    response = client.post(
        f"/pharmacy/prescriptions/{prescription['id']}/dispense",
        headers=_auth_headers(pharmacist_username),
        json={
            "items": [
                {
                    "prescription_item_id": prescription["items"][0]["id"],
                    "quantity_dispensed": 1,
                }
            ]
        },
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Pharmacy resource is outside the user's facility"


def test_dispense_rejects_insufficient_inventory(client, db_session):
    admin = _create_user(db_session, "insufficient_admin", "admin")
    pharmacist = _create_user(db_session, "insufficient_pharmacist", "pharmacist")
    doctor = _create_user(db_session, "insufficient_doctor", "doctor")
    patient = _create_user(db_session, "insufficient_patient", "patient")
    admin_username = admin.username
    pharmacist_username = pharmacist.username
    doctor_username = doctor.username
    doctor_id = doctor.id
    patient_id = patient.id
    encounter = _create_encounter(db_session, patient_id, doctor_id)
    encounter_id = encounter.id
    inventory = _create_inventory(client, admin_username, quantity_on_hand=2)
    prescription = _create_prescription(client, doctor_username, patient_id, doctor_id, encounter_id, inventory["id"])

    response = client.post(
        f"/pharmacy/prescriptions/{prescription['id']}/dispense",
        headers=_auth_headers(pharmacist_username),
        json={
            "items": [
                {
                    "prescription_item_id": prescription["items"][0]["id"],
                    "quantity_dispensed": 6,
                }
            ]
        },
    )

    assert response.status_code == 409
    assert response.json()["detail"] == "Insufficient medication inventory"


def test_admin_pharmacy_metrics(client, db_session):
    admin = _create_user(db_session, "pharmacy_metrics_admin", "admin")
    pharmacist = _create_user(db_session, "pharmacy_metrics_pharmacist", "pharmacist")
    doctor = _create_user(db_session, "pharmacy_metrics_doctor", "doctor")
    patient = _create_user(db_session, "pharmacy_metrics_patient", "patient")
    admin_username = admin.username
    pharmacist_username = pharmacist.username
    doctor_username = doctor.username
    doctor_id = doctor.id
    patient_id = patient.id
    encounter = _create_encounter(db_session, patient_id, doctor_id)
    encounter_id = encounter.id
    inventory = _create_inventory(client, admin_username)
    prescription = _create_prescription(client, doctor_username, patient_id, doctor_id, encounter_id, inventory["id"])
    client.post(
        f"/pharmacy/prescriptions/{prescription['id']}/dispense",
        headers=_auth_headers(pharmacist_username),
        json={
            "items": [
                {
                    "prescription_item_id": prescription["items"][0]["id"],
                    "quantity_dispensed": 6,
                }
            ]
        },
    )

    response = client.get("/pharmacy/admin/metrics", headers=_auth_headers(admin_username))

    assert response.status_code == 200
    payload = response.json()
    assert payload["total_inventory_items"] == 1
    assert payload["total_prescriptions"] == 1
    assert payload["dispensed_prescriptions"] == 1
    assert payload["low_stock_items"] == 0
    assert "clinician" in payload["clinical_safety_note"].lower()


def test_pharmacy_metrics_are_facility_scoped_for_pharmacist(client, db_session):
    primary_facility = _create_facility(db_session, "Pharmacy Metrics Primary")
    other_facility = _create_facility(db_session, "Pharmacy Metrics Other")
    primary_id = primary_facility.id
    other_id = other_facility.id
    pharmacist = _create_user(db_session, "pharmacy_metrics_primary_staff", "pharmacist", facility_id=primary_id)
    other_pharmacist = _create_user(db_session, "pharmacy_metrics_other_staff", "pharmacist", facility_id=other_id)
    doctor = _create_user(db_session, "pharmacy_metrics_primary_doctor", "doctor", facility_id=primary_id)
    other_doctor = _create_user(db_session, "pharmacy_metrics_other_doctor", "doctor", facility_id=other_id)
    patient = _create_user(db_session, "pharmacy_metrics_primary_patient", "patient", facility_id=primary_id)
    other_patient = _create_user(db_session, "pharmacy_metrics_other_patient", "patient", facility_id=other_id)
    pharmacist_username = pharmacist.username
    other_pharmacist_username = other_pharmacist.username
    doctor_username = doctor.username
    other_doctor_username = other_doctor.username
    doctor_id = doctor.id
    other_doctor_id = other_doctor.id
    patient_id = patient.id
    other_patient_id = other_patient.id
    encounter = _create_encounter(db_session, patient_id, doctor_id, facility_id=primary_id)
    other_encounter = _create_encounter(db_session, other_patient_id, other_doctor_id, facility_id=other_id)
    encounter_id = encounter.id
    other_encounter_id = other_encounter.id
    inventory = _create_inventory(client, pharmacist_username, "Primary Metrics Paracetamol")
    other_inventory = _create_inventory(client, other_pharmacist_username, "Other Metrics Paracetamol")
    prescription = _create_prescription(
        client,
        doctor_username,
        patient_id,
        doctor_id,
        encounter_id,
        inventory["id"],
    )
    other_prescription = _create_prescription(
        client,
        other_doctor_username,
        other_patient_id,
        other_doctor_id,
        other_encounter_id,
        other_inventory["id"],
    )
    client.post(
        f"/pharmacy/prescriptions/{prescription['id']}/dispense",
        headers=_auth_headers(pharmacist_username),
        json={"items": [{"prescription_item_id": prescription["items"][0]["id"], "quantity_dispensed": 6}]},
    )
    client.post(
        f"/pharmacy/prescriptions/{other_prescription['id']}/dispense",
        headers=_auth_headers(other_pharmacist_username),
        json={"items": [{"prescription_item_id": other_prescription["items"][0]["id"], "quantity_dispensed": 6}]},
    )

    response = client.get("/pharmacy/admin/metrics", headers=_auth_headers(pharmacist_username))

    assert response.status_code == 200
    payload = response.json()
    assert payload["total_inventory_items"] == 1
    assert payload["total_prescriptions"] == 1
    assert payload["dispensed_prescriptions"] == 1
    assert payload["total_dispense_records"] == 1
