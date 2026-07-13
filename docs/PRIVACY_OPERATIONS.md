# Privacy Operations

This document describes the current backend support for privacy deletion planning. It is not legal advice, a certification, or approval to delete clinical records automatically.

## Current Backend Capability

- `backend/privacy_operations.py` builds a non-destructive patient deletion propagation plan.
- `GET /admin/privacy/deletion-plan/{patient_id}` returns the plan to authenticated admins only.
- Facility-scoped admins can only generate plans for patients in their facility.
- The response is aggregate and PHI-safe: it returns counts, surfaces, and required actions, not names, emails, clinical text, measurements, or vector payloads.

## Surfaces Covered

- Patient account row.
- Health records and chat logs.
- Appointments, encounters, admissions, clinical orders, care events, monitoring, diagnostics, prescriptions, dispensing, billing, discharge, and nursing rows.
- Interoperability consents and export manifests.
- ABDM consent lifecycle events.
- Vector-store records linked to health-record IDs.
- Lakehouse datasets that need delete, anonymize, or tombstone propagation.
- Backup and restore policy review.
- Audit-log retention review for PHI-minimized security and compliance evidence.

## Operating Rule

The deletion plan is a review artifact. It does not delete records. A production destructive workflow must be approved per hospital contract, launch country, legal hold, retention schedule, backup policy, and incident-response requirements.

## Required Production Runbook

Before enabling destructive deletion, operators must document:

- Request intake and identity verification.
- Contract and jurisdiction review.
- Legal hold and medical-record-retention checks.
- Database delete or anonymization procedure.
- Vector-store deletion procedure.
- Lakehouse delete, anonymization, or tombstone procedure across raw, curated, and analytics zones.
- Export-recipient reconciliation for FHIR, ABDM, SMART on FHIR, DICOMweb, and partner system artifacts.
- Backup retention and restore suppression policy.
- PHI-safe audit event retained for accountability.
- Post-deletion verification evidence.

## Reference Posture

- India DPDP requires security safeguards and erasure when consent is withdrawn or the specified purpose no longer applies, subject to legal retention requirements.
- GDPR Article 17 gives a right to erasure with important exceptions, including legal obligations and public-health grounds.
- HIPAA gives access, amendment, and accounting rights over designated record sets; deletion and retention are usually governed by provider obligations, state law, contracts, and the BAA.

Official references:

- India DPDP Act, 2023: https://www.indiacode.nic.in/handle/123456789/22037
- India DPDP Rules, 2025: https://www.meity.gov.in/documents/act-and-policies/digital-personal-data-protection-rules-2025-gDOxUjMtQWa?pageTitle=Digital-Personal-Data-Protection-Rules-2025686cadad39.pdf
- GDPR Article 17: https://eur-lex.europa.eu/eli/reg/2016/679/oj
- HHS HIPAA Privacy Rule: https://www.hhs.gov/hipaa/for-professionals/privacy/index.html
- HHS HIPAA right of access: https://www.hhs.gov/hipaa/for-professionals/privacy/guidance/access/index.html
