# Appointment Workflow Hardening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make doctor listing and appointment scheduling use backend-owned doctor metadata and enforce safe time-slot rules.

**Architecture:** Add doctor specialization to the `User` model and migration map, expose it through profile and doctor schemas, and centralize appointment parsing/slot validation in `backend/appointments.py`. Tests drive behavior through the FastAPI client using isolated database fixtures and mocked email delivery.

**Tech Stack:** FastAPI, SQLAlchemy, Pydantic, pytest, Python datetime.

---

## File Structure

- Modify `backend/models.py`: add `User.specialization`.
- Modify `backend/schemas.py`: allow profile updates to include `specialization`.
- Modify `backend/main.py`: add migration entry for `users.specialization`.
- Modify `backend/auth.py`: include `specialization` in profile response.
- Modify `backend/appointments.py`: derive doctor specialization/name, reject missing doctor id, past appointments, and duplicate active slots.
- Modify `tests/unit/test_appointment_privacy.py`: add appointment workflow tests.

---

### Task 1: Add Red Appointment Workflow Tests

**Files:**
- Modify: `tests/unit/test_appointment_privacy.py`

- [x] **Step 1: Extend test helpers**

Update `_create_user` to accept doctor metadata:

```python
def _create_user(
    db_session,
    username: str,
    role: str,
    *,
    full_name: str | None = None,
    specialization: str | None = None,
) -> models.User:
    user = models.User(
        username=username,
        email=f"{username}@example.com",
        full_name=full_name,
        hashed_password=auth.get_password_hash("StrongPassword123!"),
        role=role,
        specialization=specialization,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user
```

Update `_booking_payload` to use a stable far-future date and allow spoofed specialist text:

```python
def _booking_payload(
    doctor_id: int | None,
    reason: str = "Follow-up",
    *,
    date: str = "2099-06-01",
    time: str = "09:00",
    specialist: str = "General Physician",
) -> dict:
    return {
        "doctor_id": doctor_id,
        "specialist": specialist,
        "date": date,
        "time": time,
        "reason": reason,
    }
```

- [x] **Step 2: Add red tests**

Add:

```python
def test_doctor_listing_returns_stored_specialization_and_fallback(client, db_session):
    cardiologist = _create_user(
        db_session,
        "cardio_doc",
        "doctor",
        full_name="Dr Cardio",
        specialization="Cardiology",
    )
    generalist = _create_user(db_session, "general_doc", "doctor", full_name="Dr General")

    response = client.get("/appointments/doctors")

    assert response.status_code == 200
    doctors = {doctor["id"]: doctor for doctor in response.json()}
    assert doctors[cardiologist.id]["full_name"] == "Dr Cardio"
    assert doctors[cardiologist.id]["specialization"] == "Cardiology"
    assert doctors[generalist.id]["specialization"] == "General Physician"
```

Add:

```python
def test_patient_booking_uses_doctor_specialization_not_client_specialist(client, db_session):
    patient = _create_user(db_session, "authoritative_patient", "patient")
    doctor = _create_user(
        db_session,
        "authoritative_doctor",
        "doctor",
        full_name="Dr Heart",
        specialization="Cardiology",
    )

    with patch("backend.email_service.send_booking_confirmation") as send_email:
        response = client.post(
            "/appointments/",
            json=_booking_payload(
                doctor.id,
                reason="Chest discomfort follow-up",
                specialist="Dermatology",
            ),
            headers=_auth_headers(patient.username),
        )

    assert response.status_code == 200
    assert response.json()["specialist"] == "Cardiology"
    appointment = db_session.query(models.Appointment).one()
    assert appointment.specialist == "Cardiology"
    send_email.assert_called_once()
    assert send_email.call_args.kwargs["doctor_name"] == "Dr Heart"
```

Add:

```python
def test_patient_must_select_doctor_id(client, db_session):
    patient = _create_user(db_session, "missing_doctor_id_patient", "patient")

    with patch("backend.email_service.send_booking_confirmation") as send_email:
        response = client.post(
            "/appointments/",
            json=_booking_payload(None),
            headers=_auth_headers(patient.username),
        )

    assert response.status_code == 400
    assert response.json()["detail"] == "Selected doctor not found"
    assert db_session.query(models.Appointment).count() == 0
    send_email.assert_not_called()
```

Add:

```python
def test_patient_cannot_book_past_appointment(client, db_session):
    patient = _create_user(db_session, "past_slot_patient", "patient")
    doctor = _create_user(db_session, "past_slot_doctor", "doctor")

    with patch("backend.email_service.send_booking_confirmation") as send_email:
        response = client.post(
            "/appointments/",
            json=_booking_payload(doctor.id, date="2000-01-01", time="09:00"),
            headers=_auth_headers(patient.username),
        )

    assert response.status_code == 400
    assert response.json()["detail"] == "Appointment time must be in the future"
    assert db_session.query(models.Appointment).count() == 0
    send_email.assert_not_called()
```

Add:

```python
def test_patient_cannot_double_book_doctor_active_slot(client, db_session):
    patient = _create_user(db_session, "double_booking_patient", "patient")
    other_patient = _create_user(db_session, "double_booking_other_patient", "patient")
    doctor = _create_user(db_session, "double_booking_doctor", "doctor")
    existing = models.Appointment(
        user_id=other_patient.id,
        doctor_id=doctor.id,
        specialist="General Physician",
        date_time=datetime(2099, 6, 1, 9, 0),
        reason="Existing appointment",
        status="Scheduled",
    )
    db_session.add(existing)
    db_session.commit()

    with patch("backend.email_service.send_booking_confirmation") as send_email:
        response = client.post(
            "/appointments/",
            json=_booking_payload(doctor.id),
            headers=_auth_headers(patient.username),
        )

    assert response.status_code == 409
    assert response.json()["detail"] == "Doctor already has an active appointment at that time"
    assert db_session.query(models.Appointment).count() == 1
    send_email.assert_not_called()
```

Add:

```python
def test_patient_can_book_cancelled_slot(client, db_session):
    patient = _create_user(db_session, "cancelled_slot_patient", "patient")
    other_patient = _create_user(db_session, "cancelled_slot_other_patient", "patient")
    doctor = _create_user(db_session, "cancelled_slot_doctor", "doctor")
    cancelled = models.Appointment(
        user_id=other_patient.id,
        doctor_id=doctor.id,
        specialist="General Physician",
        date_time=datetime(2099, 6, 1, 9, 0),
        reason="Cancelled appointment",
        status="Cancelled",
    )
    db_session.add(cancelled)
    db_session.commit()

    with patch("backend.email_service.send_booking_confirmation"):
        response = client.post(
            "/appointments/",
            json=_booking_payload(doctor.id),
            headers=_auth_headers(patient.username),
        )

    assert response.status_code == 200
    assert db_session.query(models.Appointment).count() == 2
```

Add:

```python
def test_reschedule_rejects_past_slot(client, db_session):
    patient = _create_user(db_session, "reschedule_past_patient", "patient")
    doctor = _create_user(db_session, "reschedule_past_doctor", "doctor")
    appointment = _create_appointment(db_session, patient, doctor, "Future visit")

    response = client.put(
        f"/appointments/{appointment.id}/reschedule",
        params={"date": "2000-01-01", "time": "09:00"},
        headers=_auth_headers(patient.username),
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Appointment time must be in the future"
```

Add:

```python
def test_reschedule_rejects_duplicate_active_doctor_slot(client, db_session):
    patient = _create_user(db_session, "reschedule_duplicate_patient", "patient")
    other_patient = _create_user(db_session, "reschedule_duplicate_other", "patient")
    doctor = _create_user(db_session, "reschedule_duplicate_doctor", "doctor")
    appointment = _create_appointment(db_session, patient, doctor, "Move me")
    other = models.Appointment(
        user_id=other_patient.id,
        doctor_id=doctor.id,
        specialist="General Physician",
        date_time=datetime(2099, 6, 2, 10, 0),
        reason="Existing slot",
        status="Rescheduled",
    )
    db_session.add(other)
    db_session.commit()

    response = client.put(
        f"/appointments/{appointment.id}/reschedule",
        params={"date": "2099-06-02", "time": "10:00"},
        headers=_auth_headers(patient.username),
    )

    assert response.status_code == 409
    assert response.json()["detail"] == "Doctor already has an active appointment at that time"
```

- [x] **Step 3: Run red tests**

Run:

```bash
python -m pytest tests/unit/test_appointment_privacy.py -q
```

Expected: FAIL because `User.specialization` does not exist and appointment validation is not implemented.

---

### Task 2: Add Doctor Specialization Metadata

**Files:**
- Modify: `backend/models.py`
- Modify: `backend/schemas.py`
- Modify: `backend/main.py`
- Modify: `backend/auth.py`

- [x] **Step 1: Add model and schema fields**

In `backend/models.py`, add:

```python
specialization = Column(String, nullable=True)
```

near `consultation_fee`.

In `backend/schemas.py`, add to `UserProfileUpdate`:

```python
specialization: Optional[str] = None
```

- [x] **Step 2: Add migration entry**

In `backend/main.py` `required_columns`, add:

```python
"specialization": "VARCHAR",
```

- [x] **Step 3: Return specialization from profile**

In `backend/auth.py` `get_user_profile`, add:

```python
"specialization": current_user.specialization,
```

- [x] **Step 4: Run focused tests**

Run:

```bash
python -m pytest tests/unit/test_appointment_privacy.py -q
```

Expected: remaining failures should now be appointment behavior, not missing model fields.

---

### Task 3: Make Appointment Booking Authoritative

**Files:**
- Modify: `backend/appointments.py`

- [x] **Step 1: Add appointment constants and helpers**

Add near imports:

```python
ACTIVE_APPOINTMENT_STATUSES = ("Scheduled", "Rescheduled")
DEFAULT_SPECIALIZATION = "General Physician"
PAST_APPOINTMENT_DETAIL = "Appointment time must be in the future"
DUPLICATE_APPOINTMENT_DETAIL = "Doctor already has an active appointment at that time"
```

Add helpers:

```python
def _parse_appointment_datetime(date: str, time: str) -> datetime:
    dt_str = f"{date} {time}"
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"):
        try:
            return datetime.strptime(dt_str, fmt)
        except ValueError:
            continue
    raise HTTPException(status_code=400, detail="Invalid date/time format")


def _doctor_specialization(doctor: models.User) -> str:
    specialization = (doctor.specialization or "").strip()
    return specialization or DEFAULT_SPECIALIZATION


def _doctor_display_name(doctor: models.User) -> str:
    return doctor.full_name or doctor.username


def _ensure_future_slot(appointment_dt: datetime) -> None:
    if appointment_dt <= datetime.now():
        raise HTTPException(status_code=400, detail=PAST_APPOINTMENT_DETAIL)


def _ensure_doctor_slot_available(
    db: Session,
    doctor_id: int,
    appointment_dt: datetime,
    *,
    exclude_appointment_id: int | None = None,
) -> None:
    query = db.query(models.Appointment).filter(
        models.Appointment.doctor_id == doctor_id,
        models.Appointment.date_time == appointment_dt,
        models.Appointment.status.in_(ACTIVE_APPOINTMENT_STATUSES),
    )
    if exclude_appointment_id is not None:
        query = query.filter(models.Appointment.id != exclude_appointment_id)
    if query.first():
        raise HTTPException(status_code=409, detail=DUPLICATE_APPOINTMENT_DETAIL)
```

- [x] **Step 2: Update `create_appointment`**

Use the helper to parse the date/time. Reject `doctor_id is None` through the existing doctor lookup. After the doctor lookup:

```python
specialization = _doctor_specialization(doctor)
_ensure_future_slot(appointment_dt)
_ensure_doctor_slot_available(db, doctor.id, appointment_dt)
```

Set:

```python
doctor_id=doctor.id,
specialist=specialization,
```

In the email call, use:

```python
doctor_name=_doctor_display_name(doctor),
```

- [x] **Step 3: Update doctor listing**

Set:

```python
specialization=_doctor_specialization(doc),
```

- [x] **Step 4: Update reschedule**

Use `_parse_appointment_datetime`, `_ensure_future_slot`, and `_ensure_doctor_slot_available` with `exclude_appointment_id=appt.id` when `appt.doctor_id` is present.

- [x] **Step 5: Run focused tests**

Run:

```bash
python -m pytest tests/unit/test_appointment_privacy.py -q
```

Expected: PASS.

---

### Task 4: Verification And Commit

**Files:**
- All files touched above.

- [x] **Step 1: Run verification**

Run:

```bash
python -m py_compile backend/appointments.py backend/auth.py backend/main.py backend/models.py backend/schemas.py
python -m pytest tests/unit/test_appointment_privacy.py -q
python -m pytest tests/unit -q
python -m pytest tests/integration tests/test_api.py -q
python scripts/sync_agent_adapters.py --check
git diff --check -- backend/appointments.py backend/auth.py backend/main.py backend/models.py backend/schemas.py tests/unit/test_appointment_privacy.py docs/superpowers/plans/2026-05-24-appointment-workflow-hardening.md
```

Expected: all commands pass.

- [ ] **Step 2: Stage only appointment workflow files**

Run:

```bash
git add -- backend/appointments.py backend/auth.py backend/main.py backend/models.py backend/schemas.py tests/unit/test_appointment_privacy.py docs/superpowers/plans/2026-05-24-appointment-workflow-hardening.md
git diff --cached --stat
```

Expected: staged files are limited to the appointment workflow implementation and plan.

- [ ] **Step 3: Commit**

Run:

```bash
git commit -m "feat: harden appointment scheduling workflow"
```

Expected: commit succeeds on `codex/appointment-workflow-hardening`.

---

## Self-Review Notes

- Spec coverage: model/schema/migration sync, profile response, doctor listing, appointment creation, past-slot validation, duplicate-slot validation, reschedule validation, and tests are all covered.
- Scope: no frontend redesign, no payment workflow, no calendar integration.
- Type consistency: the model, schema, and route code all use the field name `specialization`; duplicate slot helpers use `doctor_id`, `date_time`, and active statuses exactly as in the models.
