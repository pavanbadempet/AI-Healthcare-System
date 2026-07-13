# Sales Readiness Package Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the product easier to sell to clinics by adding an India-first market readiness API and practical sales/security/pilot documentation.

**Architecture:** Add a static admin-only readiness router in `backend/sales_readiness.py`, mount it in `backend/main.py`, test admin access and safe claims, and document the clinic sales packet.

**Tech Stack:** FastAPI, pytest, Markdown docs.

---

## File Structure

- Add `backend/sales_readiness.py`: admin-only market readiness matrix.
- Modify `backend/main.py`: mount the readiness router.
- Modify `backend/AGENTS.md` and `backend/CONTEXT.md`: document module ownership.
- Add `tests/unit/test_sales_readiness.py`: focused endpoint tests.
- Add `docs/SALES_READINESS_INDIA_FIRST.md`.
- Add `docs/SECURITY_QUESTIONNAIRE.md`.
- Add `docs/CLINIC_PILOT_PLAYBOOK.md`.
- Add `docs/PRICING_AND_PACKAGING.md`.
- Add `docs/CONTRACT_PACKET_CHECKLIST.md`.

---

### Task 1: Add Red Tests

- [x] Test that patient users cannot read `/admin/sales-readiness`.
- [x] Test that admin users receive an India-first market plan.
- [x] Test that the endpoint does not claim certifications or approvals not obtained.
- [x] Run focused tests and confirm the endpoint is missing.

### Task 2: Implement Admin Readiness API

- [x] Add static readiness matrix with India, EU, US, and other-country tracks.
- [x] Include safe product positioning and blocked claims.
- [x] Include required artifacts and next sales actions.
- [x] Mount router in `backend/main.py`.
- [x] Update backend module references.

### Task 3: Add Sales Packet Docs

- [x] Add India-first sales readiness plan.
- [x] Add clinic security questionnaire.
- [x] Add clinic pilot playbook.
- [x] Add pricing and packaging guidance.
- [x] Add contract packet checklist.

### Task 4: Verification

- [x] Run focused sales-readiness tests.
- [x] Run related trust/auth/admin tests.
- [x] Run compile, adapter sync, and diff checks.
- [x] Run broader unit and integration checks if practical.
