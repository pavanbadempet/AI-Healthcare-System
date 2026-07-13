# Diagnostics Workflow Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add the lab/radiology diagnostic result lifecycle on top of hospital operations orders.

**Architecture:** Add `DiagnosticResult` persisted records, schemas for result posting and review, and a `backend/diagnostics.py` router for doctor/admin result posting, patient-scoped result access, assigned-doctor review, and admin metrics.

**Tech Stack:** FastAPI, SQLAlchemy, Pydantic, pytest.

---

## File Structure

- Modify `backend/models.py`: add `DiagnosticResult`.
- Modify `backend/schemas.py`: add diagnostic result create/review/response schemas.
- Add `backend/diagnostics.py`: diagnostics result lifecycle router.
- Modify `backend/main.py`: mount diagnostics router.
- Modify `backend/AGENTS.md` and `backend/CONTEXT.md`: module references.
- Add `tests/unit/test_diagnostics.py`: lifecycle and access tests.
- Add `docs/DIAGNOSTICS_WORKFLOW.md`: product boundary and workflow notes.

---

### Task 1: Add Red Tests

- [x] Patient cannot post a diagnostic result.
- [x] Doctor posts result and order is completed.
- [x] Patient sees only own diagnostic results.
- [x] Assigned doctor reviews diagnostic result.
- [x] Unassigned doctor cannot review diagnostic result.
- [x] Admin diagnostics metrics summarize results.
- [x] Run focused tests and confirm routes are missing.

### Task 2: Add Model And Schemas

- [x] Add `DiagnosticResult`.
- [x] Add result create schema.
- [x] Add review update schema.
- [x] Add result response schema.

### Task 3: Implement Diagnostics Router

- [x] Add result posting endpoint.
- [x] Complete diagnostic order when result is posted.
- [x] Emit care events for posted and reviewed results.
- [x] Add patient result endpoint.
- [x] Add assigned-doctor patient result endpoint.
- [x] Add review endpoint.
- [x] Add admin metrics endpoint.
- [x] Mount router in `backend/main.py`.

### Task 4: Documentation

- [x] Add diagnostics workflow doc.
- [x] Update backend module references.

### Task 5: Verification

- [x] Run focused diagnostics tests.
- [x] Run compile checks.
- [x] Run related hospital/monitoring/admin/trust tests.
- [x] Run full unit suite and integration/API tests.
- [x] Run adapter sync and diff checks.
