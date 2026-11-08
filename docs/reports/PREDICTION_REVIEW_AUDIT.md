# Prediction Review Audit

`POST /predict/reviews` lets an assigned doctor or admin record whether an AI-assisted prediction was:

- `accepted`
- `overridden`
- `ignored`

## Access Control

- Patients cannot record review decisions.
- Doctors must be assigned to the patient through an encounter, admission, clinical order, or appointment.
- Admins can record review decisions within their normal facility boundary.

## Audit Boundary

The route writes a `REVIEW_AI_PREDICTION` audit event with safe metadata: screening area, decision, use category, model card ID, whether an external reference was present, and whether review text was provided.

Raw prediction payloads, patient names, email addresses, and review-note text are not stored in audit details.
