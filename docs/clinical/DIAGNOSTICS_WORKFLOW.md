# Diagnostics Workflow

This module closes the loop for lab, radiology, imaging, and diagnostic orders. It connects clinical orders to posted results, clinician review, patient-scoped result access, timeline events, and admin diagnostics metrics.

## Product Boundary

Safe positioning:

> Diagnostic workflow management for posting, reviewing, and tracking results under clinician supervision.

Do not claim:

- autonomous interpretation
- automatic diagnosis
- replacement of radiologists, pathologists, or doctors
- guaranteed abnormality detection
- regulatory-cleared diagnostic AI

## Core Concepts

| Concept | Purpose |
| --- | --- |
| Clinical Order | Doctor/admin-created request for lab, radiology, imaging, or diagnostic work |
| Diagnostic Result | Posted result tied to an order and patient |
| Review Status | `pending_review`, `reviewed`, or local workflow status |
| Care Event | Patient timeline event when a result is posted or reviewed |
| Metrics | Aggregate diagnostics throughput and review backlog |

## Implemented API Surface

Results:

- `POST /diagnostics/results` - doctor/admin posts result for diagnostic order
- `GET /diagnostics/patient/results` - current patient sees own results
- `GET /diagnostics/doctor/patients/{patient_id}/results` - assigned doctor/admin result view
- `PUT /diagnostics/results/{result_id}/review` - assigned doctor/admin marks review

Admin:

- `GET /diagnostics/admin/metrics` - total results, pending review, abnormal count, result type mix

## Workflow

1. Doctor/admin creates a clinical order through `/hospital/orders`.
2. Doctor/admin posts a result through `/diagnostics/results`.
3. The order is marked `completed`.
4. A patient timeline event is written.
5. Result starts as `pending_review`.
6. Assigned doctor reviews the result.
7. Review action writes a second patient timeline event.
8. Admin metrics show throughput and pending review backlog.

## Safety Language

Use:

- "posted result"
- "pending clinician review"
- "reviewed by clinician"
- "abnormal flag for review"
- "not an AI diagnosis"

Avoid:

- "diagnosed"
- "confirmed disease"
- "automatic radiology interpretation"
- "doctor replacement"

## Roadmap

Next diagnostics capabilities:

- Structured lab panels and reference ranges.
- Radiology report upload and report text extraction.
- Result amendment history.
- Critical-result acknowledgment workflow.
- Department turnaround-time analytics.
- Patient-friendly explanation after doctor review.
- ABDM/FHIR diagnostic report export.
