# Nursing Workflow

This module adds nurse task assignment, nurse worklists, task completion, patient-visible task history, doctor review views, care timeline events, and nursing operations metrics.

## Product Boundary

Safe positioning:

> Nursing workflow management for care-team task assignment, completion tracking, and operational visibility.

Do not claim:

- autonomous nursing care
- automatic clinical task prioritization
- replacement of nurses or doctors
- emergency escalation clearance
- regulatory medical-device triage

## Core Concepts

| Concept | Purpose |
| --- | --- |
| Nursing Task | Care coordination task tied to a patient and optional encounter/admission |
| Assigned Nurse | Nurse responsible for the task |
| Task Status | `assigned` or `completed` in the current workflow |
| Completion Note | Staff-entered record of task completion |
| Care Event | Timeline event when a nursing task is created or completed |
| Metrics | Assigned/completed/overdue tasks and type mix |

## Implemented API Surface

Tasks:

- `POST /nursing/tasks` - assigned doctor/admin creates a nursing task
- `GET /nursing/nurse/tasks` - nurse sees assigned worklist
- `PUT /nursing/tasks/{task_id}/complete` - assigned nurse/admin completes a task
- `GET /nursing/patient/tasks` - current patient sees own task history
- `GET /nursing/doctor/patients/{patient_id}/tasks` - assigned doctor/admin reviews patient tasks

Metrics:

- `GET /nursing/admin/metrics` - admin nursing operations summary

## Workflow

1. Doctor or admin creates a task for a patient and optional admission/encounter.
2. Task is assigned to a nurse.
3. A care event is written for patient timeline visibility.
4. Nurse sees the task in their worklist.
5. Assigned nurse completes the task with an optional completion note.
6. A completion care event is written.
7. Patient can see own task history.
8. Assigned doctor can review patient task activity.
9. Admin metrics summarize workload and completion state.

## Safety Language

Use:

- "nursing task assigned"
- "task completed by staff"
- "care coordination"
- "requires licensed staff completion"
- "operational visibility"

Avoid:

- "AI nurse"
- "automatic care completed"
- "safe without staff review"
- "nurse replacement"

## Roadmap

Next nursing capabilities:

- Shift/team assignment.
- Recurring task schedules.
- Medication administration records.
- Escalation rules for overdue critical tasks.
- Nurse handoff notes.
- Real-time worklist updates.
