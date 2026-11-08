# Care Event Feeds

This module exposes role-scoped care-event feeds for operational dashboards. It turns the shared `care_events` timeline into a polling-friendly read API for patients, assigned doctors, and administrators.

## Product Boundary

Safe positioning:

> Operational care-event feeds for dashboard updates and care-team visibility.

Do not claim:

- guaranteed real-time delivery
- emergency alerting certification
- autonomous triage
- clinical decision replacement

## Core Concepts

| Concept | Purpose |
| --- | --- |
| Care Event | Existing shared timeline event emitted by hospital workflows |
| Cursor | `after_id` lets dashboards poll only new events |
| Patient Feed | Current patient's own timeline events |
| Doctor Feed | Assigned doctor view for a specific patient |
| Admin Feed | Hospital-wide recent event feed |
| Metrics | Event counts grouped by type and severity |

## Implemented API Surface

Feeds:

- `GET /events/patient/feed` - current patient timeline feed
- `GET /events/doctor/patients/{patient_id}/feed` - assigned doctor/admin patient feed
- `GET /events/admin/recent` - admin hospital-wide recent event feed

Metrics:

- `GET /events/admin/metrics` - admin event type/severity summary

## Workflow

1. Workflow modules write `CareEvent` rows.
2. Dashboards poll with optional `after_id`.
3. Response includes ordered events and `next_after_id`.
4. Clients store `next_after_id` and request new events later.
5. Access remains scoped by role and patient assignment.

## Safety Language

Use:

- "care-event feed"
- "dashboard polling"
- "operational timeline"
- "requires clinician review"

Avoid:

- "certified emergency alerting"
- "automatic triage"
- "guaranteed live monitoring"
- "diagnostic event stream"

## Roadmap

Next event-feed capabilities:

- SSE/WebSocket streaming transport.
- Department and role filters.
- Event acknowledgments.
- Event retention policy.
- Dashboard unread counters.
