# Interoperability Consent Control Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add patient-granted consent artifacts and enforce active consent before assigned doctors or admins export patient interoperability bundles.

**Architecture:** Extend the existing interoperability module with a persisted `InteroperabilityConsent` model, consent endpoints, active-consent checks, export consent logging, and admin visibility.

**Tech Stack:** FastAPI, SQLAlchemy, Pydantic, pytest.

---

## File Structure

- Modify `backend/interoperability.py`: consent endpoints, active consent checks, export consent logging.
- Modify `backend/models.py`: add `InteroperabilityConsent` and `InteroperabilityExport.consent_id`.
- Modify `backend/schemas.py`: add consent schemas and export `consent_id`.
- Modify `backend/main.py`: startup migration for `interoperability_exports.consent_id`.
- Modify `tests/unit/test_interoperability.py`: consent grant, revoke, status, and export gating tests.
- Modify `docs/INTEROPERABILITY_EXPORTS.md`: consent workflow and API surface.

---

### Task 1: Add Red Tests

- [x] Patient can grant and list interoperability consent.
- [x] Assigned doctor cannot export without active consent.
- [x] Assigned doctor can export with active consent and export log includes consent id.
- [x] Revoked consent blocks doctor export.
- [x] Assigned doctor can view active consent status.

### Task 2: Implement Consent Controls

- [x] Add consent model and schema.
- [x] Add patient grant/list/revoke consent endpoints.
- [x] Add assigned doctor/admin consent-status endpoint.
- [x] Enforce active consent for doctor/admin bundle exports.
- [x] Persist export `consent_id` and audit consent grant/revoke/export events.
- [x] Add admin consent list and consent-aware metrics.

### Task 3: Documentation

- [x] Update interoperability export docs.
- [x] Update backend module references.
- [x] Update hospital operations foundation.

### Task 4: Verification

- [x] Run focused interoperability tests.
- [x] Run compile checks.
- [x] Run related hospital/care-event/trust tests.
- [x] Run full unit suite and integration/API tests.
- [x] Run adapter sync and diff checks.
