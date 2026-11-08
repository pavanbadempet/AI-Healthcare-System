# Discharge Workflow

This module closes inpatient episodes with clinician-authored discharge summaries, admission finalization, bed release, patient discharge records, doctor review views, and discharge metrics.

## Product Boundary

Safe positioning:

> Discharge workflow management for clinician-authored summaries and operational admission closure.

Do not claim:

- automated discharge decisioning
- AI-authored final discharge orders
- replacement of doctors or nurses
- emergency safety clearance
- regulatory medical-device discharge approval

## Core Concepts

| Concept | Purpose |
| --- | --- |
| Discharge Summary | Clinician-authored record tied to an admission and optional encounter |
| Draft Status | Summary is prepared but not patient-visible as finalized discharge record |
| Finalized Status | Summary is finalized, admission is discharged, and bed is released |
| Admission Closure | Active admission moves to `discharged` with `discharged_at` timestamp |
| Bed Release | Occupied bed becomes `available` and clears current patient |
| Metrics | Draft/finalized summary count and active/discharged admission count |

## Implemented API Surface

Summaries:

- `POST /discharge/summaries` - assigned doctor/admin drafts discharge summary
- `PUT /discharge/summaries/{summary_id}/finalize` - assigned doctor/admin finalizes discharge
- `GET /discharge/patient/summaries` - current patient sees finalized own summaries
- `GET /discharge/doctor/patients/{patient_id}/summaries` - assigned doctor/admin review view

Metrics:

- `GET /discharge/admin/metrics` - admin discharge operations summary

## Workflow

1. Patient has an active admission.
2. Assigned doctor drafts a discharge summary.
3. Draft writes a patient timeline care event.
4. Doctor finalizes the summary.
5. Admission becomes `discharged`.
6. Occupied bed becomes `available`.
7. Encounter is closed when attached to the summary.
8. Finalized summary becomes visible to the patient.
9. Admin metrics show discharge workload and active admission state.

## Safety Language

Use:

- "clinician-authored discharge summary"
- "discharge finalized"
- "admission closed"
- "bed released"
- "requires clinician finalization"

Avoid:

- "AI discharged the patient"
- "safe to go home automatically"
- "doctor replacement"
- "emergency clearance"

## Roadmap

Next discharge capabilities:

- Nursing checklist before finalization.
- Billing clearance gate before bed release.
- Structured medication reconciliation.
- Follow-up appointment generation.
- Final discharge PDF export.
- FHIR Encounter and Composition export.
