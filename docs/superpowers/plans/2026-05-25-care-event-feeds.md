# Care Event Feeds Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add role-scoped care-event feeds for dashboards so patients, assigned doctors, and administrators can poll operational activity from the shared timeline.

**Architecture:** Reuse the existing `CareEvent` model and add a `backend/care_events.py` router with cursor-based feed endpoints and admin event metrics.

**Tech Stack:** FastAPI, SQLAlchemy, Pydantic, pytest.

---

## File Structure

- Add `backend/care_events.py`: role-scoped care-event feeds and metrics.
- Modify `backend/main.py`: mount care-events router.
- Modify `backend/AGENTS.md` and `backend/CONTEXT.md`: module references.
- Add `tests/unit/test_care_events.py`: feed and access tests.
- Add `docs/CARE_EVENT_FEEDS.md`: product boundary and workflow notes.

---

### Task 1: Add Red Tests

- [x] Patient event feed is scoped to current patient.
- [x] Admin recent feed supports `after_id` cursor.
- [x] Assigned doctor can view patient event feed.
- [x] Unassigned doctor cannot view patient event feed.
- [x] Admin event metrics group by type and severity.

### Task 2: Implement Care Event Router

- [x] Add patient feed endpoint.
- [x] Add doctor patient feed endpoint.
- [x] Add admin recent endpoint.
- [x] Add admin metrics endpoint.
- [x] Add cursor response with `next_after_id`.
- [x] Mount router in `backend/main.py`.

### Task 3: Documentation

- [x] Add care-event feed doc.
- [x] Update backend module references.
- [x] Update hospital operations roadmap.

### Task 4: Verification

- [x] Run focused care-event tests.
- [x] Run compile checks.
- [x] Run related hospital/nursing/monitoring tests.
- [x] Run full unit suite and integration/API tests.
- [x] Run adapter sync and diff checks.
