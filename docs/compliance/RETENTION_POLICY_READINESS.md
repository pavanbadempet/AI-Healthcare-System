# Retention Policy Readiness

This document describes backend readiness metadata for record retention and legal-hold handling. It is not a legal retention schedule and it does not execute deletion, anonymization, archive, or legal-hold workflows.

## Backend Capability

- `backend/retention_policy.py` reads deployment runbook environment settings.
- `GET /admin/retention-readiness` returns the readiness report to authenticated admins only.
- `GET /admin/operational-health` includes `retention_policy_readiness_available`.
- The report does not expose patient identifiers, clinical data, owner contacts, runbook URLs, legal-hold URLs, or secrets.

## Required Evidence

Set these values in the deployment environment when a production operator has verified them:

- `RETENTION_POLICY_ENABLED`
- `RETENTION_OWNER_CONTACT`
- `RETENTION_RUNBOOK_URL`
- `LEGAL_HOLD_PROCESS_URL`
- `PATIENT_RECORD_RETENTION_YEARS`
- `CHAT_LOG_RETENTION_DAYS`
- `AUDIT_LOG_RETENTION_DAYS`
- `INTEROPERABILITY_EXPORT_RETENTION_DAYS`
- `VECTOR_STORE_RETENTION_DAYS`
- `LAKEHOUSE_RETENTION_DAYS`

## Surfaces Covered

- Patient medical and account records.
- AI chat logs and conversational context.
- PHI-minimized security and compliance audit logs.
- FHIR, ABDM, and partner export manifests.
- Derived vector-search records.
- Raw, curated, and analytics lakehouse datasets.

## Production Expectations

- Retention windows must be approved per hospital contract and launch country.
- Legal hold must block destructive actions until reviewed.
- Retention enforcement should coordinate with privacy deletion plans, backup restore controls, and lakehouse tombstones.
- Destructive workflows must produce PHI-safe audit evidence without storing raw clinical payloads in logs or tickets.

## Official References

- India DPDP Act, 2023: https://www.indiacode.nic.in/handle/123456789/22037
- GDPR Article 5 storage limitation and Article 17 erasure: https://eur-lex.europa.eu/eli/reg/2016/679/oj
- HHS HIPAA Privacy Rule: https://www.hhs.gov/hipaa/for-professionals/privacy/index.html
- HHS HIPAA Security Rule: https://www.hhs.gov/hipaa/for-professionals/security/index.html
