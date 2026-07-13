# Security Assurance Readiness

This document describes backend readiness metadata for security assurance evidence. It is not a scanner, SBOM generator, penetration-test report, SOC 2 report, HITRUST certification, or legal opinion.

## Backend Capability

- `backend/security_assurance.py` reads deployment evidence environment settings.
- `GET /admin/security-assurance` returns the readiness report to authenticated admins only.
- `GET /admin/operational-health` includes `security_assurance_readiness_available`.
- The report does not expose patient identifiers, clinical data, owner contacts, evidence URLs, scanner secrets, or raw findings.

## Required Evidence

Set these values in the deployment environment when a production operator has verified them:

- `SECURITY_ASSURANCE_ENABLED`
- `SECURITY_OWNER_CONTACT`
- `SECURITY_RUNBOOK_URL`
- `SECRET_SCAN_LAST_RUN_AT`
- `DEPENDENCY_SCAN_LAST_RUN_AT`
- `SBOM_GENERATED_AT`
- `VULNERABILITY_SCAN_LAST_RUN_AT`
- `PEN_TEST_REPORT_URL`
- `SECURITY_FINDINGS_OPEN_CRITICAL`
- `SECURITY_FINDINGS_OPEN_HIGH`

## Controls Covered

- Secret scan evidence.
- Dependency scan evidence.
- Software bill of materials evidence.
- Vulnerability scan evidence.
- Penetration-test report evidence.
- Open critical finding count.
- Open high finding count.

## Production Expectations

- Production launch should be blocked while open critical or high findings remain unless a named risk owner accepts a documented exception.
- SBOM and dependency scan evidence should be regenerated for each production release.
- Secret scans should run before source pushes and release packaging.
- Penetration-test evidence should be scoped to the target deployment and buyer risk profile.
- Raw scanner findings must not include PHI, patient examples, credentials, or unredacted infrastructure details in ordinary logs.

## Official References

- CISA SBOM guidance: https://www.cisa.gov/sbom
- NIST SP 800-218 Secure Software Development Framework: https://csrc.nist.gov/pubs/sp/800/218/final
- HHS HIPAA Security Rule: https://www.hhs.gov/hipaa/for-professionals/security/index.html
- HHS HIPAA Risk Analysis guidance: https://www.hhs.gov/hipaa/for-professionals/security/guidance/guidance-risk-analysis/index.html
