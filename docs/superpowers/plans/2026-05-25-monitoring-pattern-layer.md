# Monitoring Pattern Layer Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add real-time vitals capture, deterministic clinician-review monitoring signals, doctor review views, and admin aggregate pattern summaries.

**Architecture:** Extend SQLAlchemy models and Pydantic schemas with `VitalObservation` and `MonitoringSignal`. Add `backend/monitoring.py` with role-aware vitals submission, patient-scoped vitals view, assigned-doctor signal view, doctor pattern summary, and admin batch-pattern summary.

**Tech Stack:** FastAPI, SQLAlchemy, Pydantic, pytest.

---

## File Structure

- Modify `backend/models.py`: add `VitalObservation` and `MonitoringSignal`.
- Modify `backend/schemas.py`: add vitals/signal schemas.
- Add `backend/monitoring.py`: monitoring routes and signal generation.
- Modify `backend/main.py`: mount monitoring router.
- Modify `backend/AGENTS.md` and `backend/CONTEXT.md`: module references.
- Add `tests/unit/test_monitoring.py`: access and pattern tests.
- Add `docs/REALTIME_MONITORING_AND_PATTERNS.md`: product boundary and architecture.

---

### Task 1: Add Red Tests

- [x] Patient can submit own vitals and receives clinician-review signals.
- [x] Patient cannot submit vitals for another patient.
- [x] Assigned doctor can submit and review patient signals.
- [x] Unassigned doctor cannot review patient signals.
- [x] Patient vitals view is scoped to current patient.
- [x] Admin pattern summary aggregates vitals and signals.
- [x] Run focused tests and confirm routes are missing.

### Task 2: Add Models And Schemas

- [x] Add `VitalObservation`.
- [x] Add `MonitoringSignal`.
- [x] Add create/response schemas and submission response.

### Task 3: Implement Monitoring Router

- [x] Add vitals submission endpoint.
- [x] Add deterministic signal generation.
- [x] Emit care events for vitals and signals.
- [x] Add patient vitals endpoint.
- [x] Add assigned-doctor patient signal endpoint.
- [x] Add doctor pattern endpoint.
- [x] Add admin pattern endpoint.
- [x] Mount router in `backend/main.py`.

### Task 4: Documentation

- [x] Add monitoring/pattern architecture note.
- [x] Update backend module references.

### Task 5: Verification

- [x] Run focused monitoring tests.
- [x] Run compile checks.
- [x] Run related hospital/admin/trust/sales tests.
- [x] Run full unit suite and integration/API tests.
- [x] Run adapter sync and diff checks.
