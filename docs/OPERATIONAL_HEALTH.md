# Operational Health

`GET /admin/operational-health` returns a PHI-safe backend readiness report for administrators.

## Checks

- Database reachability.
- Duplicate API route registrations.
- Expected browser security headers.
- AI function registry validation.
- Data quality report availability and score summary.
- ABDM readiness evaluation without exposing credentials.
- DICOMweb readiness evaluation without exposing PACS tokens or pixel data.
- SMART on FHIR readiness evaluation without exposing client secrets or exchanging tokens.
- Backup and restore readiness evaluation without executing backups or exposing credentials, owner contacts, or runbook URLs.
- Incident response and alert readiness evaluation without sending alerts or exposing contacts, channels, runbook URLs, or webhook secrets.
- Retention policy readiness evaluation without executing deletes, archives, or legal-hold workflows.
- Security assurance readiness evaluation without running scanners or exposing contacts, URLs, or secrets.

## Privacy Boundary

The endpoint returns aggregate readiness signals only. It does not return patient names, emails, ABHA addresses, clinical free text, raw vitals, provider API keys, ABDM secrets, backup credentials, retention workflow secrets, incident webhook secrets, security scanner secrets, owner-contact values, channel names, or runbook URLs.

API middleware also assigns a PHI-safe `X-Request-ID` to each HTTP response and stores it on `request.state.request_id` for log correlation. Unsafe inbound request IDs are replaced instead of echoed.

## Status Values

- `healthy` - all checks passed.
- `degraded` - at least one check has a warning, such as data-quality issues.
- `unhealthy` - at least one core readiness check failed.
