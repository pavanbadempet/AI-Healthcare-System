# Interoperability Export Filters Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add resource-type and department filters to interoperability exports so hospitals can scope bundles to the minimum practical data set.

**Architecture:** Extend existing export endpoints with query parameters, apply filters during bundle construction, persist filter metadata on the export log, and include filters in signed manifest metadata.

**Tech Stack:** FastAPI, SQLAlchemy, Pydantic, pytest.

---

## File Structure

- Modify `backend/interoperability.py`: filter parsing, bundle filtering, manifest filter metadata.
- Modify `backend/models.py`: add `InteroperabilityExport.filter_summary`.
- Modify `backend/schemas.py`: expose export `filter_summary`.
- Modify `backend/main.py`: startup migration for `filter_summary`.
- Modify `tests/unit/test_interoperability.py`: resource-type, department, and invalid-filter tests.
- Modify `docs/INTEROPERABILITY_EXPORTS.md`: filter workflow and query parameters.

---

### Task 1: Add Red Tests

- [x] Patient can export only selected resource types.
- [x] Patient can export records scoped to one department.
- [x] Unsupported resource type filters are rejected.
- [x] Export log stores filter summary.
- [x] Manifest includes filter metadata.

### Task 2: Implement Filters

- [x] Add filter summary field to export model/schema.
- [x] Add startup migration for filter summary.
- [x] Parse and validate comma-separated resource types.
- [x] Apply resource and department filters during bundle generation.
- [x] Persist filters in export log and manifest metadata.

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
