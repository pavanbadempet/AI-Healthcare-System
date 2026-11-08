# Production Readiness Gate

This project must not be deployed to production until every gate below is verified and recorded for the target environment. A passing local test run is necessary, but it is not enough for a hospital or clinic rollout.

## Backend Code Gate

- Unit suite passes with `python -m pytest tests\unit -q`.
- Production readiness checker passes with `python scripts\production_readiness_check.py`.
- Duplicate route check reports no duplicate method/path pairs.
- Route inventory reports public, authenticated, role-scoped, and websocket route counts for review.
- Object-ID route inventory reports patient, user, and domain object identifier counts for BOLA review, with role-specific route buckets for admin, doctor/admin, billing/admin, pharmacy/admin, nurse/admin, owner, owner/admin, and scoped export access.
- Object-ID route inventory blocks public routes with patient, user, or domain object identifiers.
- Object-ID route inventory also blocks generic authenticated object routes until they are explicitly classified as admin, staff, owner, patient, doctor/admin, or scoped-export access.
- `git diff --check -- backend tests scripts docs README.md` passes.
- Backend route handlers use `Depends(database.get_db)` for database sessions.
- AI provider calls go through `backend/core_ai.py`.
- AI-generated health advice includes a medical disclaimer and clinician recommendation.

## Database Gate

- Target `DATABASE_URL` points to the intended managed database, not SQLite.
- `SECRET_KEY` and database credentials are environment-only and production-grade.
- Migrations or startup schema logic have been tested against a clone of the target database.
- Backup, restore, point-in-time recovery, retention, and deletion procedures are documented by the operator.
- Backup readiness metadata is configured for the deployment, including provider, region, retention, latest successful backup, restore test, encryption, owner, and runbook evidence.
- Admin privacy deletion plans are reviewed for each launch workflow and cover database rows, vector records, lakehouse datasets, interoperability artifacts, backups, and audit retention.
- Retention readiness metadata is configured for patient records, chat logs, audit logs, interoperability exports, vector records, lakehouse datasets, owner, runbook, and legal-hold process.
- Database access is least-privilege by service account and facility/tenant boundary.
- No local `healthcare.db`, SQLite WAL, screenshots, fixtures, or debug dumps are used as production data sources.

## Lakehouse And Data Processing Gate

- Raw, curated, and analytics zones are separated by storage path and access policy.
- Delta/lakehouse writes are dry-run tested with synthetic data before real hospital feeds.
- Batch and streaming jobs do not log names, emails, DOBs, tokens, raw clinical notes, or unredacted payloads.
- Schema evolution rules are documented before ingestion starts.
- Data quality checks cover null rates, duplicate IDs, timestamp drift, facility IDs, and patient/user joins.
- Data quality reports include OpenLineage-shaped events and aggregate quarantine metadata without raw records.
- Terminology mappings are validated against buyer/national terminology services before production exchange.
- DICOMweb/PACS metadata links are validated against the buyer archive conformance statement before image exchange.
- SMART on FHIR launch settings are validated against buyer EHR registration, redirect URI, scopes, and token-storage design before enablement.
- ABDM consent callback handling is validated in sandbox and production bridge endpoints add gateway authentication before external callbacks are enabled.
- Retention, deletion, and export processes are aligned to each hospital contract and launch country.
- Lakehouse deletion propagation uses the privacy deletion plan before any destructive job runs.

## Monitoring Gate

- API health checks, telemetry snapshots, audit logs, and alert channels are configured for the target environment.
- API responses include a PHI-safe `X-Request-ID` for log and incident correlation.
- Incident readiness metadata is configured for owner, channel, runbook, severity matrix, breach contact, and alert thresholds.
- Admin telemetry is facility-scoped and tested with at least two synthetic facilities.
- Error logs are reviewed for PII leakage before launch.
- Operational dashboards cover API latency, error rate, database health, queue/job failures, AI provider failures, and data pipeline freshness.
- Alerts have named owners, escalation timing, and an incident channel.

## Security Gate

- `SECRET_KEY`, database credentials, payment credentials, AI provider keys, email credentials, and webhook secrets are environment-only.
- CORS origins, trusted hosts, rate limits, security headers, and cookie/session settings match the target environment.
- Admin, doctor, nurse, billing, pharmacy, and patient roles are tested in the target environment.
- Facility isolation is tested with at least two synthetic facilities and cross-facility access attempts.
- Route auth classification is reviewed against the intended public, admin, patient, doctor/admin, and authenticated surfaces.
- Patient, user, and domain object identifier routes are reviewed for broken object-level authorization before launch.
- External API calls are mocked in tests and reviewed before live enablement.
- Audit logs are PHI-safe and do not contain raw clinical data or credentials.
- A vulnerability scan, dependency review, and secret scan are recorded before launch.
- Security assurance readiness metadata is configured for secret scan, dependency scan, SBOM, vulnerability scan, penetration-test evidence, and zero open critical/high findings.

## AI Safety Gate

- AI predictions are presented as review/support information, not autonomous diagnosis.
- Doctor review is required for clinical decisions, treatment, diagnosis, discharge, and emergency guidance.
- Provider calls go through `backend/core_ai.py`.
- Prompts are managed in `backend/prompt_registry.py`, not in route handlers.
- Prompt-injection guardrails are tested for retrieved records, RAG memory, web context, and uploaded reports.
- External search and logging do not receive patient identifiers.
- Model fallback behavior is tested when cloud, local, and RAG providers are unavailable.
- RAG retrieval access-control tests cover user and facility document filtering.
- Clinical risk copy is reviewed for the target buyer and launch country before sales demos.

## Operations Gate

- Rollback procedure is documented and rehearsed against the target deployment path.
- Incident response contacts, support ownership, and escalation timing are documented.
- Hospital pilot acceptance criteria are written before go-live.
- Country-specific legal, privacy, and clinical-claims signoff is recorded before launch.
- Data processing agreement, security questionnaire, pricing/package terms, and support terms are ready for the buyer.
- Production launch is blocked until a named owner signs each gate with date, environment, and evidence link.
