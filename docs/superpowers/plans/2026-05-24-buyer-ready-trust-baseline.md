# Buyer-Ready Trust Baseline Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a capital-light trust baseline that makes the product more credible for small clinic sales without claiming external certification.

**Architecture:** Introduce a reusable PHI-safe audit utility, expose admin audit review, write audit events for sensitive health and admin actions, and document a clinic-facing security packet.

**Tech Stack:** FastAPI, SQLAlchemy, pytest, Markdown docs.

---

## File Structure

- Add `backend/audit.py`: centralized sanitized audit logging and response shaping.
- Modify `backend/auth.py`: audit login, profile update, and admin sensitive-data access.
- Modify `backend/chat.py`: audit health-record creation/deletion, chat-history deletion, and report downloads.
- Modify `backend/admin.py`: add admin audit review endpoint and audit user role/deletion changes.
- Add `tests/unit/test_trust_baseline.py`: focused trust-baseline tests.
- Add `docs/TRUST_BASELINE.md`: clinic-facing posture and deployment checklist.

---

### Task 1: Add Red Trust-Baseline Tests

- [x] Add audit sanitizer test proving emails, dates of birth, tokens, phone numbers, and clinical free text are not persisted in audit details.
- [x] Add admin audit route authorization test.
- [x] Add admin audit review test proving returned logs are sanitized.
- [x] Add health-record create/delete audit coverage test.
- [x] Run `python -m pytest tests/unit/test_trust_baseline.py -q` and confirm failure before implementation.

### Task 2: Implement Centralized Audit Logging

- [x] Add `backend/audit.py`.
- [x] Implement `sanitize_audit_details()`.
- [x] Implement `record_audit_event()` as best-effort persistence that never exposes raw exception text.
- [x] Implement `audit_log_to_response()`.

### Task 3: Wire Sensitive Actions

- [x] Replace one-off login and full-details audit writes with `record_audit_event()`.
- [x] Audit profile updates by field name only, not values.
- [x] Audit health-record creation and deletion without storing clinical input or prediction output.
- [x] Audit chat-history deletion and health-report downloads.
- [x] Audit admin role updates and user deletion.
- [x] Add `GET /admin/audit-logs` with admin-only access, pagination, and simple filters.

### Task 4: Add Trust Packet

- [x] Add `docs/TRUST_BASELINE.md`.
- [x] Clearly state non-claims: no SOC 2, HITRUST, HIPAA certification, FDA clearance, or clinical validation package.
- [x] Include deployment requirements, BAA readiness items, incident response steps, and known gaps.

### Task 5: Verification

- [x] Run focused tests.
- [x] Run related auth/admin/chat tests.
- [x] Run broader unit and integration checks when practical.
- [x] Run compile and adapter sync checks.
- [x] Review diff for accidental PHI or unrelated churn before final response.
