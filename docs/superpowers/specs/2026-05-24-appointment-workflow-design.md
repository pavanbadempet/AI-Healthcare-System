# Appointment Workflow Hardening Design

Date: 2026-05-24
Status: Approved design, pending implementation plan

## Goal

Make the telemedicine appointment workflow authoritative and doctor-aware. The backend should use stored doctor metadata and scheduling rules instead of accepting client-supplied specialist text or hardcoded doctor specialization.

## Scope

This spec covers:

- `backend/models.py`
- `backend/schemas.py`
- `backend/main.py`
- `backend/auth.py`
- `backend/appointments.py`
- focused appointment tests under `tests/unit/`
- frontend API tests only if the backend response contract changes

This spec does not add calendar integrations, recurring availability blocks, payment capture, or video-provider provisioning.

## Current Problem

`GET /appointments/doctors` currently returns `"General Physician"` for every doctor. `POST /appointments/` accepts `specialist` from the client and stores it directly on the appointment. That allows stale or incorrect appointment metadata and keeps the telemedicine workflow closer to a UI shell than a reliable scheduling system.

## Recommended Approach

Add doctor specialization as first-class user metadata and make the appointment router derive appointment specialist details from the selected doctor record.

Doctor metadata will be stored on `users.specialization`. Existing doctors without this value will continue to display `"General Physician"` as a fallback. Patients will still book by selecting a real doctor id, and the backend will decide the displayed specialist string.

## Data Model

Add `specialization` to the `User` SQLAlchemy model:

```python
specialization = Column(String, nullable=True)
```

Update startup migration logic in `backend/main.py` so existing databases receive the `users.specialization` column.

No new appointment table column is required. `Appointment.specialist` remains the denormalized display value for historical appointments, but new appointments must set it from the selected doctor's stored specialization.

## API Contract

### Doctor Profile

`GET /profile` should return `specialization` for the current user.

`PUT /profile` should allow doctors and admins to update `specialization` through `UserProfileUpdate`. Patients may also send the field, but it should not affect role-based access; it is only surfaced by doctor listing for users whose role is `doctor`.

### Doctor Listing

`GET /appointments/doctors` should return doctors with:

- `id`
- `full_name`
- `specialization`
- `consultation_fee`
- `profile_picture`

The specialization value should be `doctor.specialization` when present, otherwise `"General Physician"`.

### Appointment Creation

`POST /appointments/` should:

- require `doctor_id`
- reject missing or non-doctor users
- parse `date` and `time` using the existing accepted formats
- reject appointments in the past
- reject duplicate active appointments for the same doctor at the same date/time
- derive `specialist` from the selected doctor's specialization fallback
- use the selected doctor's display name in booking emails

Active duplicate statuses are `Scheduled` and `Rescheduled`. `Cancelled` appointments should not block a new booking for the same slot.

### Appointment Reschedule

`PUT /appointments/{appointment_id}/reschedule` should apply the same future-date and duplicate active slot checks as creation. The duplicate check must ignore the appointment being rescheduled.

## Access Control

Keep existing listing rules:

- admins list all appointments
- doctors list only assigned appointments
- patients list only their own appointments

Keep existing owner/admin update/delete permissions in this slice. Doctor-side appointment modification can be added in a later care-team workflow spec.

## Error Handling

Use stable, non-sensitive client errors:

- invalid date/time: `400 Invalid date/time format`
- missing/non-doctor doctor id: `400 Selected doctor not found`
- past slot: `400 Appointment time must be in the future`
- duplicate active slot: `409 Doctor already has an active appointment at that time`

Do not log patient names, appointment reasons, or raw exception text.

## Testing

Follow TDD:

1. Add failing tests for doctor listing returning stored specialization.
2. Add failing tests proving appointment creation ignores client-supplied specialist text and stores the doctor's specialization.
3. Add failing tests for missing `doctor_id`.
4. Add failing tests for past appointment rejection.
5. Add failing tests for duplicate active doctor slot rejection.
6. Add failing tests for reschedule past/duplicate validation.

Focused verification:

```bash
python -m pytest tests/unit/test_appointment_privacy.py -q
```

Broader verification:

```bash
python -m pytest tests/unit -q
python -m pytest tests/integration tests/test_api.py -q
python scripts/sync_agent_adapters.py --check
```

## Out Of Scope

- Availability calendars
- Appointment reminders
- Payment authorization
- Jitsi/meeting link persistence
- Doctor modification permissions
- Frontend UI redesign
- External EHR scheduling integration

## Acceptance Criteria

- Doctor listing no longer hardcodes every specialization.
- New appointments use doctor-owned specialization and name.
- Past appointments are rejected.
- Duplicate active doctor slots are rejected.
- Reschedule applies the same slot validation.
- Models, schemas, and startup migration logic remain in sync.
- Relevant tests pass without external services.
