# Interoperability Exports Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add standards-friendly patient bundle exports so hospitals can inspect and map patient data for EHR/HIS integrations without claiming certification.

**Architecture:** Add an `InteroperabilityExport` audit model plus a `backend/interoperability.py` router that builds FHIR-style bundles from existing hospital workflow tables.

**Tech Stack:** FastAPI, SQLAlchemy, Pydantic, pytest.

---

## File Structure

- Add `backend/interoperability.py`: FHIR-style bundle export endpoints and metrics.
- Modify `backend/models.py`: add `InteroperabilityExport`.
- Modify `backend/schemas.py`: add export response schema.
- Modify `backend/main.py`: mount interoperability router.
- Modify `backend/AGENTS.md` and `backend/CONTEXT.md`: module references.
- Add `tests/unit/test_interoperability.py`: export and access tests.
- Add `docs/INTEROPERABILITY_EXPORTS.md`: product boundary and workflow notes.

---

### Task 1: Add Red Tests

- [x] Patient can export own FHIR-style bundle.
- [x] Assigned doctor can export patient bundle.
- [x] Unassigned doctor cannot export patient bundle.
- [x] Patient cannot access interoperability metrics.
- [x] Admin can review export metrics.

### Task 2: Implement Export Router

- [x] Add export log model and response schema.
- [x] Build FHIR-style bundle from patient, encounter, observation, diagnostics, pharmacy, billing, and care-event data.
- [x] Add patient bundle endpoint.
- [x] Add assigned doctor/admin bundle endpoint.
- [x] Add admin metrics endpoint.
- [x] Record export log and PHI-safe audit event.
- [x] Mount router in `backend/main.py`.

### Task 3: Documentation

- [x] Add interoperability export doc.
- [x] Update backend module references.
- [x] Update hospital operations roadmap.

### Task 4: Verification

- [x] Run focused interoperability tests.
- [x] Run compile checks.
- [x] Run related hospital/care-event/trust tests.
- [x] Run full unit suite and integration/API tests.
- [x] Run adapter sync and diff checks.
