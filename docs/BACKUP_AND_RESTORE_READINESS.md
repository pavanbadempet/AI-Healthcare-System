# Backup And Restore Readiness

This document describes the backend readiness metadata for backup, restore, and retention evidence. It is not backup execution, disaster recovery automation, or a legal retention schedule.

## Backend Capability

- `backend/backup_readiness.py` reads deployment runbook environment settings.
- `GET /admin/backup-readiness` returns the readiness report to authenticated admins only.
- `GET /admin/operational-health` includes `backup_readiness_available`.
- The report does not expose backup credentials, owner contact values, runbook URLs, patient identifiers, or clinical data.

## Required Evidence

Set these values in the deployment environment when a production operator has verified them:

- `BACKUP_ENABLED`
- `BACKUP_PROVIDER`
- `BACKUP_STORAGE_REGION`
- `BACKUP_RETENTION_DAYS`
- `BACKUP_LAST_SUCCESS_AT`
- `BACKUP_RESTORE_TESTED_AT`
- `BACKUP_ENCRYPTION_ENABLED`
- `BACKUP_OWNER_CONTACT`
- `BACKUP_RUNBOOK_URL`

The backend treats restore tests older than 90 days as stale readiness evidence. A stale or missing restore test does not break the API, but it marks backup readiness as action required.

## Production Expectations

- Backups must be encrypted and access-controlled.
- Restore testing must be rehearsed before production clinical data is accepted.
- RTO and RPO targets must be agreed in the hospital or clinic contract.
- Backup restoration must not reintroduce deleted patient data outside an approved rollback window.
- Restore evidence should be linked from the release gate, not pasted into logs or tickets if it contains sensitive infrastructure details.

## Official References

- HHS HIPAA Security Rule: https://www.hhs.gov/hipaa/for-professionals/security/index.html
- HHS ransomware and HIPAA contingency planning guidance: https://www.hhs.gov/hipaa/for-professionals/security/guidance/cybersecurity/ransomware-fact-sheet/index.html
- NIST SP 800-34 Rev. 1 contingency planning: https://csrc.nist.gov/pubs/sp/800/34/r1/upd1/final
- NIST Cybersecurity Framework Recover function: https://www.nist.gov/cyberframework/recover
