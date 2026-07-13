# Clinic Security Questionnaire

This document gives short answers for clinic buyer due diligence. It is not a certification report.

## Product Category

**What is the system?**

AI-assisted clinic workflow software for appointments, patient records, clinician-reviewed summaries, screening documentation, and report generation.

**Does it replace doctors?**

No. Doctors and qualified clinical staff remain responsible for diagnosis, treatment, emergencies, and patient communication.

**Does it independently prescribe or diagnose?**

No. Early sales must avoid autonomous diagnosis, autonomous triage, and independent prescribing claims.

## Data Handling

**What patient data can the system process?**

Account/profile data, appointment information, health-record entries, chat history if enabled, screening inputs/results, and generated reports.

**Is data used for model training?**

Not by default. Any training or analytics use requires explicit product approval, clinic approval, and privacy review.

**Can a patient or clinic request deletion?**

Yes, but destructive execution must be governed by the clinic contract and applicable retention law. Current code supports deleting chat history and individual health records, and admins can generate a PHI-safe deletion propagation plan covering database, vector-store, lakehouse, interoperability, backup, and audit-retention surfaces.

**Is data shared with third parties?**

Only configured infrastructure and AI/service providers required to run the product. The clinic-facing packet must list subprocessors before production use.

## Security Controls

**How are users authenticated?**

Users authenticate with password-based login and JWT access tokens. Passwords are hashed with bcrypt.

**Are roles enforced?**

Yes. The backend uses role checks for admin workflows and scopes patient records to the authenticated user.

**Are sensitive actions audited?**

Yes. The system writes PHI-safe audit logs for login, profile update, sensitive admin access, health-record creation/deletion, chat-history deletion, report download, role update, and user deletion.

**Can admins review audit logs?**

Yes. Admins can use `GET /admin/audit-logs`.

**Does the audit log store clinical notes or raw patient values?**

No. Audit details are sanitized before persistence and should store event metadata, not clinical content.

**Are errors safe?**

Security-focused paths avoid returning stack traces or raw provider failures to users.

## Deployment

**What must be configured before production?**

- Strong `SECRET_KEY`.
- Test mode disabled.
- HTTPS-only public access.
- Production database with backups.
- Backup readiness variables for provider, region, retention, latest successful backup, restore test, encryption, owner, and runbook evidence.
- Incident readiness variables for owner, alert channel, runbook, severity matrix, breach contact, and threshold evidence.
- Retention readiness variables for record, chat, audit, export, vector, lakehouse, owner, runbook, and legal-hold evidence.
- Security assurance variables for secret scan, dependency scan, SBOM, vulnerability scan, penetration-test evidence, and open critical/high findings.
- Restricted database credentials.
- Approved frontend origin in CORS.
- Secret storage for provider API keys.
- Hosting region and subprocessor list.

**Can we run it without cloud AI?**

The AI provider layer supports local Ollama fallback where configured. Production behavior depends on deployment choices and model availability.

**Is there a production checklist?**

Yes. Use `docs/TRUST_BASELINE.md` and `docs/CONTRACT_PACKET_CHECKLIST.md` before any real clinic data.

## India Readiness

**Is it ready to sell in India?**

It is ready for controlled clinic pilots if scoped as clinician-in-the-loop workflow software and if the clinic packet is completed before real patient data.

**What India-specific items are needed?**

- DPDP-aligned privacy notice.
- Data-processing terms with the clinic.
- Grievance/contact point.
- Data retention/deletion terms.
- ABDM compatibility roadmap.
- Telemedicine clinician-accountability wording if remote consultations are used.

## Europe Readiness

**Is it ready for Europe?**

Not without a GDPR and AI-risk review. Europe should be treated as a second expansion market.

**What is needed first?**

GDPR privacy notice, data-processing agreement, data subject rights workflow, cross-border transfer review, and AI Act / medical-device intended-use review.

## US Readiness

**Is it ready for US clinics?**

Not for PHI production use until BAA readiness and HIPAA Security Rule safeguards are reviewed.

**What is needed first?**

Business associate agreement readiness, HIPAA safeguard mapping, breach notification process, security risk assessment, and clinical decision support intended-use review.

## Current Gaps

- No external SOC 2 or HITRUST report.
- No formal penetration test.
- No FDA, CDSCO, or EU medical-device regulatory clearance.
- Full account export/deletion workflow still needs product implementation.
- Destructive deletion execution is not automatic yet; the current backend provides the reviewed propagation plan that an approved operator workflow must execute.
- EHR/FHIR/ABDM integration is roadmap, not complete production interoperability.
