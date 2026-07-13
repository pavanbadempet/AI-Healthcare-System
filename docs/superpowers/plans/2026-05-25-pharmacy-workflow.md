# Pharmacy Workflow Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a pharmacy workflow layer for medication inventory, clinician prescriptions, pharmacist dispensing, scoped patient/doctor views, and pharmacy metrics.

**Architecture:** Add persisted medication inventory, prescription, prescription item, and dispense record models. Add request/response schemas and a `backend/pharmacy.py` router with role-aware access controls and care events.

**Tech Stack:** FastAPI, SQLAlchemy, Pydantic, pytest.

---

## File Structure

- Modify `backend/models.py`: add pharmacy inventory, prescription, prescription item, and dispense record models.
- Modify `backend/schemas.py`: add pharmacy request/response schemas.
- Add `backend/pharmacy.py`: pharmacy workflow router.
- Modify `backend/main.py`: mount pharmacy router.
- Modify `backend/admin.py`: allow admin assignment of the `pharmacist` role.
- Modify `backend/AGENTS.md` and `backend/CONTEXT.md`: module references.
- Add `tests/unit/test_pharmacy.py`: workflow and access tests.
- Extend `tests/unit/test_admin_security.py`: pharmacist role assignment coverage.
- Add `docs/PHARMACY_WORKFLOW.md`: product boundary and workflow notes.

---

### Task 1: Add Red Tests

- [x] Patient cannot create pharmacy inventory.
- [x] Admin can create and list inventory.
- [x] Pharmacist can create inventory.
- [x] Doctor creates prescription for assigned patient.
- [x] Patient sees only own prescriptions.
- [x] Assigned doctor can view patient prescriptions.
- [x] Unassigned doctor cannot view patient prescriptions.
- [x] Pharmacist dispenses prescription and inventory decrements.
- [x] Dispense rejects insufficient inventory.
- [x] Admin pharmacy metrics summarize workflow.
- [x] Admin can assign pharmacist role.

### Task 2: Add Models And Schemas

- [x] Add `MedicationInventory`.
- [x] Add `Prescription`.
- [x] Add `PrescriptionItem`.
- [x] Add `DispenseRecord`.
- [x] Add inventory create/response schemas.
- [x] Add prescription create/item/response schemas.
- [x] Add dispense request/response schemas.

### Task 3: Implement Pharmacy Router

- [x] Add inventory create/list endpoints.
- [x] Add prescription creation endpoint.
- [x] Emit care event for prescription creation.
- [x] Add patient prescription endpoint.
- [x] Add assigned-doctor prescription endpoint.
- [x] Add dispensing endpoint with stock decrement and dispense records.
- [x] Emit care event for dispensing.
- [x] Add pharmacy metrics endpoint.
- [x] Mount router in `backend/main.py`.

### Task 4: Documentation

- [x] Add pharmacy workflow doc.
- [x] Update backend module references.
- [x] Update hospital operations roadmap.

### Task 5: Verification

- [x] Run focused pharmacy tests.
- [x] Run compile checks.
- [x] Run related hospital/diagnostics/admin/trust tests.
- [x] Run full unit suite and integration/API tests.
- [x] Run adapter sync and diff checks.
