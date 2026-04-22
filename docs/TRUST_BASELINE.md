# Buyer-Ready Trust Baseline

This packet describes the current capital-light trust posture for selling the AI Healthcare System to small clinics, with India as the first target market and Europe/US as later regulated expansion markets. It is not a SOC 2, HITRUST, HIPAA certification, FDA clearance, CE mark, CDSCO approval, or legal opinion. It is the operating baseline the product must meet before handling clinic data in a real deployment.

## Product Scope

- AI-assisted healthcare workflow system for clinics.
- Clinician-in-the-loop support for summaries, record organization, screening outputs, appointments, and patient communication.
- The system must not be marketed as autonomous diagnosis, autonomous triage, or treatment authority.
- Clinical users remain responsible for diagnosis, treatment, emergency decisions, and patient communication.

## Market Rollout Strategy

### 1. India First

India is the recommended first market because small clinics are more reachable, sales cycles are shorter than large US/EU hospitals, and a clinician-in-the-loop product can start as workflow software before pursuing medical-device-level claims.

India launch posture:

- Position as clinic workflow, patient record organization, appointment, report, and clinician-assist software.
- Align privacy operations with the Digital Personal Data Protection Act, 2023.
- Design for ABDM compatibility where useful: ABHA, consent-based sharing, facility/professional identifiers, and health-record portability.
- If offering telemedicine, keep doctors as the accountable providers and align workflows with India's Telemedicine Practice Guidelines.
- Avoid claims that the software independently diagnoses, treats, prescribes, or replaces a registered medical practitioner.
- If the intended use shifts into diagnosis/treatment software, review CDSCO medical-device software requirements before sale.

Minimum India sales packet:

- Privacy notice and consent language.
- Data processing terms for clinics.
- Security baseline and incident response process.
- Data retention/deletion process.
- Subprocessor and hosting-region list.
- ABDM roadmap statement.
- AI clinical-safety statement: clinician reviews all outputs.

### 2. Europe Second

Europe should come after India because GDPR, EU AI Act, and medical-device rules make healthcare AI more demanding. The product can still be sold if scoped carefully, but claims and data handling must be precise.

Europe launch posture:

- Treat health data as sensitive data with GDPR-grade consent, purpose limitation, access controls, deletion/export rights, and cross-border transfer controls.
- Keep AI as assistive unless and until an MDR/AI Act pathway is deliberately pursued.
- Avoid autonomous diagnosis or triage claims.
- Prepare for high-risk AI and medical-device analysis if the software influences clinical decisions.

### 3. United States Third

The US is commercially attractive but buyer due diligence is more mature. Clinics will expect HIPAA business-associate readiness if the product handles PHI for them.

US launch posture:

- Be ready to sign a BAA before handling PHI for a covered entity.
- Maintain administrative, physical, and technical safeguards for ePHI.
- Keep clinical decision support explainable and clinician-reviewable to reduce FDA device risk.
- Avoid direct-to-consumer health-data sharing or tracking that could trigger FTC scrutiny.

### 4. Other Countries

Do not treat "rest of world" as one market. For each country, classify:

- Whether health data is specially protected.
- Whether the clinic is legally responsible for patient records.
- Whether AI/CDS software is regulated as a medical device.
- Whether telemedicine requires local clinician registration.
- Whether data must stay in-country.
- Whether breach notification is required.

## Current Technical Controls

- Role-based access control separates patient, doctor, and admin capabilities.
- Authentication uses hashed passwords and JWT access tokens.
- Sensitive admin and health-record actions are written to the `audit_logs` table.
- Audit details are sanitized before persistence to reduce PHI, PII, and secret leakage.
- Admins can review audit logs through `GET /admin/audit-logs`.
- Admins can generate PHI-safe patient deletion propagation plans through `GET /admin/privacy/deletion-plan/{patient_id}`.
- Admins can review PHI-safe backup and restore readiness metadata through `GET /admin/backup-readiness`.
- Admins can review PHI-safe incident response and alert readiness metadata through `GET /admin/incident-readiness`.
- Admins can review PHI-safe retention policy readiness metadata through `GET /admin/retention-readiness`.
- Admins can review PHI-safe security assurance readiness metadata through `GET /admin/security-assurance`.
- Health records and chat history are scoped to the authenticated user.
- Health report generation and AI responses include clinical safety framing.
- AI provider access is centralized through `backend/core_ai.py`.
- Error handling avoids returning stack traces or raw provider failures to clients.

## Audit Trail Coverage

The application records these security-relevant events:

- `LOGIN_SUCCESS`
- `UPDATE_PROFILE`
- `VIEW_SENSITIVE_DATA`
- `CREATE_HEALTH_RECORD`
- `DELETE_HEALTH_RECORD`
- `DELETE_CHAT_HISTORY`
- `DOWNLOAD_HEALTH_REPORT`
- `UPDATE_USER_ROLE`
- `DELETE_USER`

Audit records include actor user ID, target user ID, action, timestamp, and sanitized details. They intentionally avoid raw symptoms, chat messages, clinical measurements, predictions, email addresses, dates of birth, phone numbers, passwords, tokens, and API keys.

## Minimum Deployment Requirements

- Set `SECRET_KEY` to a strong production secret.
- Do not enable test mode in production.
- Use HTTPS only.
- Store production data in a managed database with encrypted storage and automated backups.
- Restrict database credentials to the deployed API service.
- Configure CORS only for the production frontend domain.
- Keep provider API keys in environment secrets, never in source code.
- Disable public database, vector-store, and admin-console access.
- Review logs weekly for PHI leakage and failed security events.
- Export and retain audit logs according to the clinic contract and applicable law.

## Clinic Sales Positioning

Use this wording:

> AI-assisted clinic workflow software that helps clinicians organize records, summarize patient context, and streamline administrative tasks while keeping clinicians in control.

Avoid this wording:

- "AI doctor"
- "replaces clinicians"
- "FDA approved"
- "HIPAA certified"
- "guaranteed diagnosis"
- "hospital-grade compliance"

## BAA Readiness Checklist

Before signing a clinic customer:

- Identify the hosting region and subprocessors.
- Document data categories processed by the system.
- Document where PHI is stored, transmitted, logged, and backed up.
- Confirm breach notification contact and timeline.
- Confirm data return/deletion process at contract termination.
- Confirm who approves deletion plans covering database, vector, lakehouse, interoperability, backup, and audit-retention surfaces.
- Confirm support access rules for production data.
- Confirm backup retention and restore process.
- Confirm latest restore-test evidence and recovery owner before production go-live.
- Confirm incident owner, alert channel, severity matrix, breach notification contact, and alert thresholds before production go-live.
- Confirm retention windows and legal-hold handling before production go-live.
- Confirm secret scan, dependency scan, SBOM, vulnerability scan, penetration-test evidence, and open critical/high finding counts before production go-live.
- Confirm audit-log retention period.

## Incident Response Checklist

If a possible data incident occurs:

- Preserve logs and affected records.
- Revoke exposed credentials or tokens.
- Disable affected accounts or integrations.
- Determine affected users, data categories, and time window.
- Notify the clinic owner/contact according to contract terms.
- Document timeline, root cause, containment, and corrective action.
- Add a regression test or control for the failure mode.

## Known Gaps

- No external SOC 2, HITRUST, or HIPAA audit has been completed.
- No FDA clearance, CE mark, CDSCO approval, or clinical validation package exists.
- No formal penetration test has been completed.
- EHR/FHIR interoperability is not production-ready.
- Multi-tenant enterprise isolation still needs a dedicated review before larger clinic groups or hospitals.
- Production monitoring and alerting need deployment-specific configuration.
- The code currently generates deletion plans; final destructive deletion execution still requires contract-specific approval, retention rules, and operator runbooks.

## Official Reference Sources

- India DPDP Act, 2023: https://www.meity.gov.in/writereaddata/files/Digital%20Personal%20Data%20Protection%20Act%202023.pdf
- India ABDM overview: https://nha.gov.in/NDHM
- India CDSCO medical-device regulation portal: https://www.cdsco.gov.in/opencms/opencms/en/Medical-Device-Diagnostics/
- India Telemedicine Practice Guidelines: https://esanjeevani.mohfw.gov.in/assets/guidelines/Telemedicine_Practice_Guidelines.pdf
- EU GDPR overview: https://commission.europa.eu/law/law-topic/data-protection/data-protection-explained_en
- EU AI in healthcare: https://health.ec.europa.eu/ehealth-digital-health-and-care/artificial-intelligence-healthcare_en
- US HIPAA Security Rule: https://www.hhs.gov/hipaa/for-professionals/security/index.html
- US HHS business associates: https://www.hhs.gov/hipaa/for-professionals/covered-entities/index.html
- US FDA clinical decision support guidance: https://www.fda.gov/regulatory-information/search-fda-guidance-documents/clinical-decision-support-software
