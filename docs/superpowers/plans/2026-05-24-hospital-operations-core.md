# Hospital Operations Core Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add the shared backend foundation for a full AI-assisted hospital/clinic operating system across OPD, IPD, emergency, diagnostics, pharmacy, doctors, patients, and administrators.

**Architecture:** Add SQLAlchemy models and Pydantic schemas for departments, beds, encounters, admissions, clinical orders, and care events. Expose a `backend/hospital_operations.py` router with role-specific patient, doctor, and admin views. Keep all insights deterministic and clinician-reviewed.

**Tech Stack:** FastAPI, SQLAlchemy, Pydantic, pytest.

---

## File Structure

- Modify `backend/models.py`: add operations tables.
- Modify `backend/schemas.py`: add request/response schemas.
- Add `backend/hospital_operations.py`: routes and role checks.
- Modify `backend/main.py`: mount router.
- Modify `backend/AGENTS.md` and `backend/CONTEXT.md`: module references.
- Add `tests/unit/test_hospital_operations.py`: role and workflow coverage.
- Add `docs/HOSPITAL_OPERATIONS_CORE.md`: architecture/product boundary.

---

### Task 1: Add Red Tests

- [x] Patient cannot manage departments.
- [x] Admin can create departments and beds.
- [x] Doctor can create encounter and patient timeline is scoped.
- [x] Doctor can create department order and view assigned patient panel.
- [x] Patient cannot create clinical orders.
- [x] Admin operations view summarizes departments, beds, encounters, admissions, and orders.
- [x] Run focused tests and confirm routes are missing.

### Task 2: Add Models And Schemas

- [x] Add `Department`.
- [x] Add `Bed`.
- [x] Add `Encounter`.
- [x] Add `Admission`.
- [x] Add `ClinicalOrder`.
- [x] Add `CareEvent`.
- [x] Add Pydantic create/response schemas.

### Task 3: Implement Router

- [x] Add department endpoints.
- [x] Add bed endpoint.
- [x] Add encounter endpoint with care event.
- [x] Add admission endpoint with bed occupancy.
- [x] Add order endpoint with care event.
- [x] Add patient timeline endpoint.
- [x] Add doctor patient panel and deterministic insights endpoints.
- [x] Add admin operations endpoint.
- [x] Mount router in `backend/main.py`.

### Task 4: Documentation

- [x] Add hospital operations architecture note.
- [x] Update backend module references.

### Task 5: Verification

- [x] Run focused hospital operations tests.
- [x] Run compile checks.
- [x] Run related admin/trust/sales tests.
- [x] Run full unit suite and integration/API tests.
- [x] Run adapter sync and diff checks.
