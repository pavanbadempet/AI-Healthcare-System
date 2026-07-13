# Data Quality and Lineage

Backend data quality reporting provides an admin-only, PHI-safe operational view over core hospital datasets.

## API

- `GET /admin/data-quality` - aggregate quality checks, dataset counts, lineage metadata, OpenLineage-shaped events, quarantine summaries, failed check IDs, and overall score.

The endpoint scopes results to the authenticated admin's `facility_id` when the admin is assigned to a facility. Global admins see aggregate counts across all facilities.

## Included Datasets

- `patient_accounts`
- `encounters`
- `vital_observations`
- `diagnostic_results`
- `prescriptions`
- `invoices`
- `interoperability_exports`

## Quality Checks

- Patient birth-date completeness.
- SpO2 range validity.
- Heart-rate range validity.
- Diagnostic summary completeness.
- Prescription item presence.
- Invoice monetary fields are non-negative.
- Interoperability export manifest integrity.

## Lineage Events

The report includes `lineage_events` shaped like OpenLineage run events with `eventType`, `eventTime`, `producer`, `schemaURL`, `run`, `job`, `inputs`, and `outputs`. Events are generated per dataset using source table names, quality output dataset names, row counts, failed check IDs, and privacy facets.

These events are compatibility payloads for downstream collectors. They do not send network requests by themselves.

## Quarantine Summary

The `quarantine` block lists failed checks and their aggregate quarantine target table names, such as `quarantine_vital_observations`. It reports counts and severity only; it does not expose invalid rows or clinical values.

## Pipeline Extraction Guardrails

`backend/data_engineering_platform.py` validates incremental JDBC extraction filters before Spark receives a query. Incremental column names must be simple SQL identifiers, existing `WHERE` clauses are extended with `AND`, and string checkpoint values are SQL-escaped before being appended to the configured query.

REST API extraction accepts only `http` and `https` base URLs and uses a bounded request timeout, defaulting to 30 seconds with `request_timeout_seconds` available for deployment-specific tuning.

Delta Lake table creation and schema-evolution helpers validate catalog/database/table/column identifiers, validate simple Delta data types, and SQL-escape external locations and column comments before issuing Spark SQL.

## Privacy Boundary

Reports return aggregate counts, check IDs, dataset names, module lineage, OpenLineage-shaped metadata, quarantine targets, and scores only. They must not return patient names, emails, free-text clinical notes, ABHA addresses, raw invalid rows, or raw clinical values.
