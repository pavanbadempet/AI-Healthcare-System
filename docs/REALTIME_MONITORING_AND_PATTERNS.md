# Real-Time Monitoring And Pattern Layer

This module adds the first real-time monitoring layer on top of the hospital operations core. It captures vitals, emits clinician-review signals, and summarizes aggregate patterns for doctors and administrators.

## Product Boundary

Safe positioning:

> Continuous clinic/hospital workflow monitoring that flags patterns for clinician review.

Do not claim:

- emergency monitoring replacement
- autonomous triage
- autonomous diagnosis
- automatic treatment decisions
- guaranteed detection

## Core Concepts

| Concept | Purpose |
| --- | --- |
| Vital Observation | Heart rate, blood pressure, SpO2, temperature, respiratory rate, source, observed time |
| Monitoring Signal | Deterministic review flag generated from vitals outside review ranges |
| Care Event | Timeline event emitted when vitals/signals are recorded |
| Doctor Pattern View | Assigned-patient monitoring summary |
| Admin Pattern View | Aggregate counts by signal type, severity, and department |

## Implemented API Surface

Vitals:

- `POST /monitoring/vitals` - patient self-submission, assigned doctor, or admin
- `GET /monitoring/patient/vitals` - current patient only

Vital submissions must include at least one measurement and must stay inside accepted capture ranges before any vital, signal, or care-event row is written.

Doctor review:

- `GET /monitoring/doctor/patients/{patient_id}/signals` - assigned doctor/admin only
- `GET /monitoring/doctor/patterns` - assigned patient summary

Admin analytics:

- `GET /monitoring/admin/patterns` - aggregate signal and vitals summary

## Signal Language

Signals must use review language:

- "needs clinician review"
- "outside the review range"
- "pattern summary"
- "not final clinical conclusions"

Avoid final clinical language:

- "diagnosed"
- "confirmed"
- "requires treatment"
- "emergency detected"

## Real-Time Direction

Current implementation writes vitals and care events synchronously to the database. The next production step is a streaming layer:

- emit event after every vital observation
- send doctor dashboard updates through SSE/WebSocket
- keep patient timeline synchronized
- keep admin dashboards updated by department

## Batch Data Direction

The current admin pattern endpoint computes aggregate summaries directly from stored observations and signals. Later batch jobs should materialize:

- signal counts by department and day
- delayed review queues
- patient follow-up gaps
- ward/bed monitoring summaries
- doctor workload patterns
- clinic-level pilot closeout reports

## Safety

All monitoring output is decision support. Doctors remain responsible for clinical decisions, emergency escalation, treatment, and patient communication.
