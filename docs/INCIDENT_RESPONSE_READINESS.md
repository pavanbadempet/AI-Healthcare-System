# Incident Response Readiness

This document describes the backend readiness metadata for incident response and alert thresholds. It is not an incident-response service, pager integration, breach notification decision, or legal opinion.

## Backend Capability

- `backend/incident_response.py` reads deployment runbook environment settings.
- `GET /admin/incident-readiness` returns the readiness report to authenticated admins only.
- `GET /admin/operational-health` includes `incident_response_readiness_available`.
- The report does not expose patient identifiers, clinical data, webhook secrets, owner contacts, channel names, breach contacts, or runbook URLs.

## Required Evidence

Set these values in the deployment environment when a production operator has verified them:

- `INCIDENT_RESPONSE_ENABLED`
- `INCIDENT_RESPONSE_OWNER_CONTACT`
- `INCIDENT_RESPONSE_CHANNEL`
- `INCIDENT_RESPONSE_RUNBOOK_URL`
- `INCIDENT_RESPONSE_SEVERITY_MATRIX_URL`
- `INCIDENT_BREACH_NOTIFICATION_CONTACT`
- `ALERT_ERROR_RATE_THRESHOLD_PERCENT`
- `ALERT_AI_FAILURE_RATE_THRESHOLD_PERCENT`
- `ALERT_PIPELINE_STALENESS_MINUTES`
- `ALERT_SECURITY_EVENT_THRESHOLD`

## Alert Coverage

The readiness report exposes configured thresholds for:

- API error rate.
- AI provider failure rate.
- Data pipeline staleness.
- Security event spikes.

It does not send alerts. Real alert delivery must be configured in the deployment platform, monitoring stack, or incident-management system.

## Incident Phases

The backend reports coverage for a practical incident lifecycle:

- Prepare.
- Detect.
- Analyze.
- Contain.
- Eradicate.
- Recover.
- Post-incident review.

## Production Expectations

- Every production environment has a named incident owner and escalation channel.
- Severity definitions are written before go-live.
- Breach-notification contacts and timelines are agreed in contract terms.
- Alert thresholds are tested with synthetic events before real clinical data is accepted.
- Incident records must avoid patient identifiers and clinical details unless legal/privacy review approves handling in a controlled system.

## Official References

- HHS HIPAA Breach Notification Rule: https://www.hhs.gov/hipaa/for-professionals/breach-notification/index.html
- HHS HIPAA Security Rule: https://www.hhs.gov/hipaa/for-professionals/security/index.html
- NIST SP 800-61 Rev. 2 Computer Security Incident Handling Guide: https://csrc.nist.gov/pubs/sp/800/61/r2/final
- NIST Cybersecurity Framework Respond function: https://www.nist.gov/cyberframework/respond
