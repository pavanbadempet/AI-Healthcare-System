# Nursing Workflow Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add nursing task workflows so doctors/admins can assign tasks, nurses can work assigned lists, patients can see own task history, and admins can track nursing workload.

**Architecture:** Add a `NursingTask` model, schemas, and a `backend/nursing.py` router with role-aware task creation, nurse assignment views, task completion, patient/doctor scoped views, and admin metrics.

**Tech Stack:** FastAPI, SQLAlchemy, Pydantic, pytest.

---

## File Structure

- Modify `backend/models.py`: add `NursingTask`.
- Modify `backend/schemas.py`: add nursing task create/complete/response schemas.
- Add `backend/nursing.py`: nursing workflow router.
- Modify `backend/main.py`: mount nursing router.
- Modify `backend/admin.py`: allow admin assignment of the `nurse` role.
- Modify `backend/AGENTS.md` and `backend/CONTEXT.md`: module references.
- Add `tests/unit/test_nursing.py`: workflow and access tests.
- Extend `tests/unit/test_admin_security.py`: nurse role assignment coverage.
- Add `docs/NURSING_WORKFLOW.md`: product boundary and workflow notes.

---

### Task 1: Add Red Tests

- [x] Patient cannot create nursing task.
- [x] Doctor creates task and nurse sees assignment.
- [x] Assigned nurse completes task.
- [x] Unassigned nurse cannot complete task.
- [x] Patient sees only own nursing tasks.
- [x] Unassigned doctor cannot view patient nursing tasks.
- [x] Admin nursing metrics summarize workflow.
- [x] Admin can assign nurse role.

### Task 2: Add Model And Schemas

- [x] Add `NursingTask`.
- [x] Add create schema.
- [x] Add completion schema.
- [x] Add response schema.

### Task 3: Implement Nursing Router

- [x] Add task creation endpoint.
- [x] Emit care event for task creation.
- [x] Add nurse worklist endpoint.
- [x] Add assigned-nurse completion endpoint.
- [x] Emit care event for task completion.
- [x] Add patient task endpoint.
- [x] Add assigned-doctor task endpoint.
- [x] Add admin metrics endpoint.
- [x] Mount router in `backend/main.py`.

### Task 4: Documentation

- [x] Add nursing workflow doc.
- [x] Update backend module references.
- [x] Update hospital operations roadmap.

### Task 5: Verification

- [x] Run focused nursing tests.
- [x] Run compile checks.
- [x] Run related hospital/monitoring/admin tests.
- [x] Run full unit suite and integration/API tests.
- [x] Run adapter sync and diff checks.
