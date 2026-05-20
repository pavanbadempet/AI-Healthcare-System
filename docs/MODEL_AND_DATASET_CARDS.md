# Model And Dataset Cards

`GET /admin/model-cards` exposes backend evidence cards for local clinical prediction models and their public training artifacts.

## Included Models

- Diabetes risk screening.
- Heart disease screening.
- Liver disease screening.
- Kidney disease screening.
- Lung health screening.

## Included Fields

Model cards include endpoint, artifact presence, model family, dataset card ID, feature count, intended use, output shape, limitations, human-review requirement, medical-disclaimer requirement, and post-deployment monitoring requirement.

Dataset cards include source, local processed artifact, task, intended use, limitations, and whether production patient data is present.

## Privacy Boundary

The endpoint does not read or return dataset rows, patient examples, names, emails, raw feature values, API keys, or production patient data. It reports only artifact metadata and governance text.

## Product Boundary

These cards support pilot review and buyer evidence. They are not a regulatory certification, external clinical validation, or claim that the models diagnose or treat disease autonomously.
