# Interoperability Export Profiles Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add reusable admin-managed export profiles so hospitals can save partner EHR/HIS export scopes and apply them consistently to patient bundle exports.

**Architecture:** Add an export profile model and schema, expose admin CRUD-light profile endpoints, allow export routes to apply active profiles, persist the profile reference on export logs, and include profile filters in signed manifest metadata.

**Tech Stack:** FastAPI, SQLAlchemy, Pydantic, pytest.

---

## File Structure

- Modify `backend/interoperability.py`: profile endpoints, profile filter parsing, export log and manifest metadata.
- Modify `backend/models.py`: add `InteroperabilityExportProfile` and export `profile_id`.
- Modify `backend/schemas.py`: add profile create/response schemas and export `profile_id`.
- Modify `backend/main.py`: startup migration for export `profile_id`.
- Modify `tests/unit/test_interoperability.py`: profile creation, authorization, and export behavior tests.
- Modify `docs/INTEROPERABILITY_EXPORTS.md`: profile workflow and query parameters.

---

### Task 1: Add Red Tests

- [x] Admin can create and list export profiles.
- [x] Non-admin users cannot create export profiles.
- [x] Doctor export can apply saved profile filters.
- [x] Export log stores the profile reference.
- [x] Manifest includes profile filter metadata.

### Task 2: Implement Export Profiles

- [x] Add export profile model and export profile relation.
- [x] Add profile schemas and startup migration.
- [x] Add admin create/list profile endpoints.
- [x] Validate saved resource filters.
- [x] Apply active profiles to patient and doctor exports.
- [x] Persist profile context in export logs and manifests.

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
