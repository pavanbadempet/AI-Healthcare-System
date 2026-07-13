# Clinic Pilot Playbook

Use this playbook to run the first India clinic pilots without over-scoping the product.

## Pilot Goal

Prove that the system saves clinic staff and clinicians time while preserving clinician control and patient-data safety.

## Pilot Timeline

| Day | Activity | Output |
| --- | --- | --- |
| 0 | Discovery and scope | Pilot goals, users, workflows |
| 1 | Demo with synthetic data | Clinic confirms fit |
| 2 | Trust packet review | Privacy/security questions answered |
| 3 | Setup | Admin account, staff roles, deployment checklist |
| 4-10 | Controlled workflow use | Appointments, records, reports, summaries |
| 11 | Mid-pilot review | Issues and adoption blockers |
| 14 | Closeout | Metrics, conversion decision |

## Pilot Scope

Include:

- Appointment booking and doctor assignment.
- Patient profile management.
- Health-record entry and retrieval.
- Clinician-reviewed AI chat/summaries.
- Report download.
- Admin audit log review.

Exclude:

- Emergency triage.
- Autonomous diagnosis.
- Prescription generation.
- Insurance claims.
- Hospital EHR integrations.
- WhatsApp/SMS automation unless separately reviewed.

## Demo Dataset

Use synthetic patients only. Do not use real names, dates of birth, phone numbers, government identifiers, addresses, or real medical histories in demos.

Synthetic demo cases:

- Adult wellness follow-up.
- Diabetes screening review.
- Cardiology follow-up with old report.
- Appointment reschedule workflow.
- Privacy opt-out behavior.

## Onboarding Checklist

- Clinic owner approves pilot scope.
- Admin user is assigned.
- Staff/doctor roles are mapped.
- Password policy is explained.
- Privacy notice is shared.
- Data-processing terms are accepted.
- Hosting region is documented.
- Support contact is shared.
- Incident contact is shared.
- Audit-log screen/API is demonstrated.

## Daily Pilot Metrics

Track:

- Appointments created.
- Appointments rescheduled/cancelled.
- Health records created.
- Reports downloaded.
- AI summary drafts reviewed by clinicians.
- AI summary drafts accepted/edited/rejected.
- Support tickets.
- Time saved estimates.

## Closeout Report

The closeout should include:

- Baseline workflow pain points.
- Usage metrics.
- Staff feedback.
- Clinician feedback.
- Security/privacy questions raised.
- Bugs and fixes.
- Conversion recommendation.
- Proposed paid plan.

## Conversion Criteria

Convert only when:

- The clinic has used at least two core workflows.
- A clinician confirms AI output is useful as a draft/assistant.
- The admin can see audit logs.
- There are no unresolved high-severity privacy/security issues.
- The clinic agrees to subscription scope and support terms.
