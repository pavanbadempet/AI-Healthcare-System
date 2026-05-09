# Signed Export Manifests Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add reproducible bundle hashes and signed export manifests so hospitals can reconcile interoperability exports without claiming regulated certification.

**Architecture:** Extend `InteroperabilityExport` with bundle hash and manifest signature metadata. Generate a canonical SHA-256 hash over the exported bundle and an HMAC-SHA256 signature over manifest metadata. Return the manifest with exports and expose a role-scoped manifest lookup endpoint.

**Tech Stack:** FastAPI, SQLAlchemy, Pydantic, pytest, Python standard library hashing/HMAC.

---

## File Structure

- Modify `backend/interoperability.py`: manifest hashing/signing, response inclusion, and manifest lookup endpoint.
- Modify `backend/models.py`: add export hash/signature fields.
- Modify `backend/schemas.py`: expose export hash/signature fields.
- Modify `backend/main.py`: startup migration for export manifest fields.
- Modify `tests/unit/test_interoperability.py`: manifest response, persistence, lookup, and access tests.
- Modify `docs/INTEROPERABILITY_EXPORTS.md`: manifest workflow and boundary language.

---

### Task 1: Add Red Tests

- [x] Export response includes a signed manifest.
- [x] Manifest bundle hash matches the response bundle hash.
- [x] Export row stores bundle hash and manifest signature.
- [x] Admin can retrieve export manifest by export id.
- [x] Unrelated patient cannot read another export manifest.

### Task 2: Implement Manifests

- [x] Add bundle hash and signature fields to export model/schema.
- [x] Compute canonical bundle SHA-256.
- [x] Sign manifest metadata with HMAC-SHA256.
- [x] Return manifest with export responses.
- [x] Add role-scoped manifest lookup endpoint.
- [x] Add startup migration for manifest fields.

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
