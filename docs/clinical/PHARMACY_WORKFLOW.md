# Pharmacy Workflow

This module adds medication inventory, clinician prescriptions, pharmacist dispensing, patient-scoped prescription access, doctor review views, and pharmacy operations metrics.

## Product Boundary

Safe positioning:

> Pharmacy workflow management for clinician-created prescriptions and pharmacist-verified dispensing.

Do not claim:

- autonomous prescribing
- automated medication safety clearance
- replacement of doctors or pharmacists
- regulator-cleared prescribing decision support
- guaranteed drug interaction detection

## Core Concepts

| Concept | Purpose |
| --- | --- |
| Medication Inventory | Stock item with strength, form, batch, quantity, reorder threshold, and status |
| Prescription | Clinician-created medication order tied to a patient and optional encounter |
| Prescription Item | Medication, dose, frequency, duration, instructions, and prescribed/dispensed quantity |
| Dispense Record | Pharmacy action recording what quantity was dispensed and by whom |
| Care Event | Patient timeline entry when a prescription is created or dispensed |
| Metrics | Inventory count, low-stock count, prescription status mix, and dispense volume |

## Implemented API Surface

Inventory:

- `POST /pharmacy/inventory` - admin/pharmacist creates a medication inventory item
- `GET /pharmacy/inventory` - doctor/pharmacist/admin lists inventory

Prescriptions:

- `POST /pharmacy/prescriptions` - assigned doctor/admin creates a prescription
- `GET /pharmacy/patient/prescriptions` - current patient sees only own prescriptions
- `GET /pharmacy/doctor/patients/{patient_id}/prescriptions` - assigned doctor/admin prescription view
- `POST /pharmacy/prescriptions/{prescription_id}/dispense` - pharmacist/admin dispenses prescription items

Metrics:

- `GET /pharmacy/admin/metrics` - pharmacy/admin operations summary

## Workflow

1. Admin or pharmacist creates medication inventory.
2. Doctor opens an encounter or otherwise becomes assigned to the patient.
3. Doctor creates a prescription with one or more items.
4. A patient timeline event is written for prescription creation.
5. Patient can view the prescription in their own scope.
6. Assigned doctor can review patient prescriptions.
7. Pharmacist dispenses against prescription items.
8. Inventory is decremented when an item is linked to stock.
9. Prescription status becomes `partially_dispensed` or `dispensed`.
10. Dispensing writes a care event and a dispense record.

## Safety Language

Use:

- "clinician-created prescription"
- "pharmacist-verified dispensing"
- "stock threshold"
- "ready for pharmacy review"
- "supports medication workflow"

Avoid:

- "AI prescribed"
- "medication approved automatically"
- "drug safety guaranteed"
- "pharmacist replacement"

## Roadmap

Next pharmacy capabilities:

- Drug catalog import and normalized medicine codes.
- Expiry-date and batch recall workflow.
- Medication administration records for inpatient care.
- Refill requests and doctor approval.
- Interaction/allergy checks as review flags only.
- ABDM/FHIR medication request and dispense export.
