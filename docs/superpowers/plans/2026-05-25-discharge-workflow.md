# Discharge Workflow Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add discharge summaries and admission closure so inpatient workflows can be finalized, beds released, and patients given clinician-authored discharge records.

**Architecture:** Add a `DischargeSummary` model, schemas, and a `backend/discharge.py` router with assigned-doctor/admin creation and finalization, patient finalized-summary access, doctor review views, and admin metrics.

**Tech Stack:** FastAPI, SQLAlchemy, Pydantic, pytest.

---

## File Structure

- Modify `backend/models.py`: add `DischargeSummary`.
- Modify `backend/schemas.py`: add discharge summary create/response schemas.
- Add `backend/discharge.py`: discharge workflow router.
- Modify `backend/main.py`: mount discharge router.
- Modify `backend/AGENTS.md` and `backend/CONTEXT.md`: module references.
- Add `tests/unit/test_discharge.py`: workflow and access tests.
- Add `docs/DISCHARGE_WORKFLOW.md`: product boundary and workflow notes.

---

### Task 1: Add Red Tests

- [x] Patient cannot create discharge summary.
- [x] Doctor creates summary for assigned admission.
- [x] Finalization closes admission and frees bed.
- [x] Patient sees only own finalized summaries.
- [x] Unassigned doctor cannot view patient summaries.
- [x] Admin discharge metrics summarize workflow.

### Task 2: Add Model And Schemas

- [x] Add `DischargeSummary`.
- [x] Add create schema.
- [x] Add response schema.

### Task 3: Implement Discharge Router

- [x] Add summary creation endpoint.
- [x] Emit care event for draft creation.
- [x] Add finalization endpoint.
- [x] Discharge admission and release bed on finalization.
- [x] Close encounter when attached.
- [x] Add patient finalized-summary endpoint.
- [x] Add assigned-doctor summary endpoint.
- [x] Add admin metrics endpoint.
- [x] Mount router in `backend/main.py`.

### Task 4: Documentation

- [x] Add discharge workflow doc.
- [x] Update backend module references.
- [x] Update hospital operations roadmap.

### Task 5: Verification

- [x] Run focused discharge tests.
- [x] Run compile checks.
- [x] Run related hospital/pharmacy/billing/admin tests.
- [x] Run full unit suite and integration/API tests.
- [x] Run adapter sync and diff checks.
