# AI Clinic Command Center Design

Date: 2026-06-02
Status: Approved design for review

## Goal

Build the first 30-day milestone toward a 10/10 AI healthcare product by focusing the existing AI Healthcare System into an India-first clinic pilot experience.

The milestone is not a full global healthcare platform. It is a buyer-demo-ready clinic workflow system that proves one complete patient visit can be run faster, more safely, and more clearly with clinician-reviewed AI support.

## Target Buyer

The first target buyer is a small clinic in India:

- Solo clinic or clinic with 1-10 doctors.
- Staff currently use paper, spreadsheets, WhatsApp, or basic appointment tools.
- Buyer can run a 14-day paid pilot.
- Synthetic data is acceptable for the first demo.
- Real patient data is handled only after privacy, consent, access, backup, and deletion expectations are agreed.

The architecture must stay capable of growing into clinic groups and hospitals, but the first milestone optimizes for real clinic value and fast feedback.

## Product Promise

The product promise for this milestone is:

> Run a patient visit faster, with organized records, clinician-reviewed AI documentation, clear follow-up actions, and a PHI-safe audit trail.

The product must not be positioned as an autonomous doctor, autonomous triage system, emergency decision system, certified medical device, or guaranteed diagnostic engine.

## North Star Workflow

The flagship workflow is a complete clinic visit:

1. Staff books or starts a patient visit.
2. Patient profile, history, vitals, and prior records are available in one place.
3. Doctor opens a visit workspace.
4. AI generates a draft summary or visit note for clinician review.
5. Doctor edits and approves the note.
6. System creates follow-up actions such as diagnostics, medication note, revisit reminder, or patient report.
7. Patient-facing report is generated with clinical safety language.
8. Sensitive actions are role-scoped and audit logged.

This workflow should be demoable in five minutes using synthetic clinic data.

## Deliberately Out Of Scope

These are out of scope for the 30-day milestone:

- Autonomous diagnosis.
- Autonomous treatment or prescription.
- Emergency triage.
- Insurance claims processing.
- Real production ABDM submission.
- Full hospital procurement workflows.
- Claims of being HIPAA-certified, SOC 2-certified, regulator-cleared, or guaranteed-accuracy software.
- Live clinical use with real patient data before pilot readiness gates are satisfied.

## Architecture

The current FastAPI backend and Next.js frontend remain the foundation. The product should be reshaped around a single clinic visit workflow instead of disconnected feature pages.

### Backend Pillars

#### Visit Workspace

Introduce or standardize a visit-centered domain object that connects:

- Facility or clinic.
- Appointment or walk-in encounter.
- Patient.
- Assigned doctor.
- Staff intake.
- Vitals.
- Prior records.
- AI draft summary.
- Doctor note.
- Diagnostics.
- Medication notes.
- Follow-up actions.
- Patient report.
- Audit trail.

The visit object becomes the central workflow unit for the clinic pilot.

#### AI Safety Gateway

All provider-backed AI continues to go through `backend/core_ai.py`.

Every clinical AI output must include:

- Draft/review-only status.
- Medical disclaimer where patient-facing or clinical advice is present.
- Clinician review requirement.
- Source or context references when available.
- Limitations or uncertainty language.
- Clean fallback when the provider is unavailable.

Prompts remain owned by `backend/prompt_registry.py`; route handlers must not inline system prompts.

#### Clinic Scope Layer

Every clinic workflow object must be facility-scoped:

- Patient.
- Appointment.
- Visit.
- Record.
- Report.
- Audit event.
- Doctor or staff action.
- AI draft.

The first milestone should make facility scoping explicit in the clinic workflow and tests. Larger multi-tenant enterprise isolation can be deepened later, but the demo and pilot surfaces must not imply cross-clinic access is acceptable.

#### Demo Mode

Demo mode must run with synthetic India-clinic data and no external API keys.

Demo mode should make these states visible:

- Synthetic data active.
- AI provider unavailable but fallback active, if applicable.
- Integrations simulated.
- No real patient data present.
- Demo readiness passed or failed.

#### Readiness Gate

The app should report one of three states:

- `demo-ready`: synthetic demo works without external dependencies.
- `pilot-ready`: configured for a controlled clinic pilot with required trust settings.
- `production-blocked`: real production use is blocked and reasons are shown.

Readiness checks should be PHI-safe and should not expose secrets.

### Frontend Pillars

#### Today's Clinic

This becomes the main buyer-facing dashboard. It should prioritize:

- Waiting queue.
- In-consultation patients.
- Pending doctor reviews.
- Follow-ups due.
- Demo or pilot readiness.
- Backend/AI degraded states.

This replaces generic hospital telemetry as the first thing a clinic buyer sees.

#### Visit Workspace

The doctor-facing visit workspace is the flagship screen. It should show:

- Patient identity and safety context.
- Reason for visit.
- Vitals.
- Prior records.
- AI draft summary.
- Doctor note editor.
- Diagnostics actions.
- Medication/follow-up actions.
- Patient report generation.
- Audit and consent context.

#### AI Clinical Assistant Panel

The AI panel should support narrow, safe actions:

- Summarize records.
- Draft visit note.
- Prepare follow-up checklist.
- Explain screening result.

It must not offer unsafe actions such as:

- Diagnose patient.
- Prescribe treatment.
- Replace doctor review.
- Emergency triage.

#### Trust Center

The trust center should show:

- Audit log coverage.
- Role access summary.
- Demo mode or real-data status.
- Backup readiness.
- Retention readiness.
- Deletion readiness.
- External integration readiness.

The language should be precise: readiness, alignment, configuration, and review status. Do not claim certification unless it has actually been obtained.

## Data Flow

The primary data flow is:

```text
Appointment or walk-in
  -> Patient
  -> Visit
  -> Records and vitals
  -> AI draft
  -> Doctor review
  -> Report and follow-up
  -> Audit log
```

The important product principle is convergence. All clinic work should converge into the visit workflow so users do not feel they are jumping across disconnected modules.

## 30-Day Implementation Scope

### Week 1: Make The Current Product Trustworthy

- Fix broken frontend tests and stale UI expectations.
- Fix healthcare trust copy, including `HIPPA` to `HIPAA` or remove the claim.
- Remove or clearly label hard-coded claims such as uptime and model accuracy.
- Add clean degraded states for backend, AI, telemetry, and integration failures.
- Add a demo readiness status.
- Ensure the app can run end to end with synthetic clinic data and no external API keys.
- Keep frontend build, lint, and focused tests green.

### Week 2: Build The Clinic Visit Workspace

- Add or standardize the visit workflow object.
- Connect visit to appointment, patient, vitals, notes, AI summary, diagnostics, medications, follow-up, report, and audit events.
- Create a doctor-facing visit page that becomes the main product experience.
- Add staff workflow for today's queue and patient intake.
- Keep every action role-scoped and facility-scoped.

### Week 3: Make AI Clinician-Grade

- AI generates draft summaries and visit notes only.
- Doctor approval is required before output becomes final or patient-facing.
- AI output includes sources, limitations, clinician-review language, and medical disclaimers where needed.
- Add audit events for AI draft generation, doctor approval, report generation, and record access.
- Add deterministic fallback behavior when providers are unavailable.

### Week 4: Make It Sellable

- Add guided demo mode with synthetic Indian clinic data.
- Add a five-minute sales demo flow.
- Add pilot readiness report.
- Add buyer-facing trust screen for audit logs, data safety, consent/readiness, backup, retention, and deletion.
- Polish the dashboard around today's clinic operations.

## Safety Rules

- AI output is always draft or review-only.
- Doctor approval is required before patient-facing output.
- Medical advice includes a disclaimer and recommends consulting a qualified clinician.
- Emergency guidance must direct users to emergency services or qualified care.
- Failed AI/provider/backend states must degrade gracefully.
- Demo mode uses synthetic data only and visibly says so.
- Patient, visit, report, and audit objects are facility-scoped.
- Tests, fixtures, docs, screenshots, and logs must not contain real patient data.

## Product Language Rules

Use:

- Clinician-reviewed AI draft.
- AI-assisted clinic workflow.
- Screening support.
- Visit documentation support.
- Readiness.
- Trust baseline.
- Synthetic demo data.

Avoid unless formally true:

- AI doctor.
- Autonomous diagnosis.
- Autonomous triage.
- Guaranteed diagnosis.
- HIPAA-certified.
- HIPAA-safe.
- SOC 2-certified.
- Regulator-cleared.
- Hospital-grade compliance.
- Guaranteed accuracy.

## Engineering Quality Gates

The 30-day milestone is not complete until these gates pass:

- One command starts backend and frontend with synthetic clinic data.
- `npm --prefix frontend run build` passes.
- Frontend lint passes.
- Frontend Jest tests pass.
- Focused backend tests for clinic workflow, auth, audit, AI safety, and facility scoping pass.
- Demo readiness check passes.
- No real PII appears in tests, fixtures, logs, docs, screenshots, or demo data.
- Unsupported compliance, uptime, or accuracy claims are removed or clearly marked as demo/sample values.
- Backend, AI, telemetry, and integration failure states are clean and buyer-safe.

## Existing Risk Signals To Address First

The prior product audit found these issues that should be handled early:

- Frontend Jest was not green.
- Full backend unit run timed out in the local shell.
- `git diff --check` failed due to trailing whitespace across many touched files.
- Login page used `HIPPA-Safe`, which is misspelled and risky as a compliance claim.
- Dashboard displayed hard-coded-looking `99.999%` uptime and `98.4%` accuracy.
- Dashboard showed raw `Failed to fetch` in a buyer-visible surface when backend was unavailable.

These do not invalidate the product direction, but they block the 10/10 milestone until cleaned up.

## Definition Of 10/10 For This Milestone

For this milestone, 10/10 means:

- A clinic buyer understands the value in five minutes.
- A doctor can complete a synthetic patient visit without broken states.
- AI clearly saves documentation time while staying clinician-reviewed.
- The product avoids unsafe medical and compliance claims.
- Trust, audit, role scope, facility scope, and readiness are visible.
- The demo works without real patient data or external API keys.
- Build and focused tests are green.

It does not mean the product has every healthcare feature. It means the first clinic workflow is powerful, credible, stable, safe, and sellable.

## Approval Gate

After this spec is reviewed and approved, the next step is to write an implementation plan. Implementation should not begin until the plan decomposes the work into small, testable slices with clear backend, frontend, safety, and demo-readiness gates.
