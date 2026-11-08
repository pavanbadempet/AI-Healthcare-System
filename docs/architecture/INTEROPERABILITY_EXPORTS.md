# Interoperability Exports

This module provides standards-friendly patient data export bundles for hospital integration mapping. It is designed for pilots where clinics and hospitals need a clear way to inspect, move, or map patient records into local EHR/HIS workflows while preserving a visible patient consent trail and export integrity manifest.

## Product Boundary

Safe positioning:

> FHIR-style patient export bundles for integration mapping and clinician-reviewed operational workflows.

Do not claim:

- FHIR certification
- ABDM certification or national health-network approval
- production EHR integration without hospital-side validation
- automated consent compliance
- autonomous diagnosis, treatment, or emergency decisioning

The export and consent records are integration aids. Hospitals still need local validation, consent workflow review, security review, and deployment approvals before production exchange.

The ABDM connector boundary is intentionally configuration-driven. It can prepare consent request payloads, record PHI-safe consent lifecycle callback metadata, and report readiness without real credentials; outbound submission remains disabled until a deployment supplies ABDM onboarding values and an access token.

## Core Concepts

| Concept | Purpose |
| --- | --- |
| FHIR-style Bundle | Collection-shaped JSON payload using familiar resource names for mapping |
| Consent Artifact | Patient-granted export permission with purpose, scope, recipient type, and revocation status |
| Export Profile | Admin-managed reusable resource and department scope for a partner EHR/HIS |
| Export Filter | Optional resource-type and department scope applied before a bundle is generated |
| Export Log | Database record of who requested a bundle, for which patient, resource count, bundle hash, and manifest signature |
| Export Manifest | Hash and signature metadata that lets a receiver reconcile an exported bundle later |
| ABDM Readiness | Admin-only check showing whether required ABDM connector settings are present without exposing secrets |
| ABDM Consent Request | Assigned-doctor/admin payload preparation for patient-consented HIU flows using supported purpose codes and HI types |
| ABDM Consent Callback | Admin-only sandbox callback ingestion for consent lifecycle status, stored as metadata and payload hashes without raw callback bodies |
| DICOMweb Readiness | Admin-only PACS/DICOMweb configuration check without exposing tokens or image data |
| DICOMweb Metadata Links | Admin-only QIDO-RS/WADO-RS/STOW-RS URL shapes for a validated StudyInstanceUID |
| SMART on FHIR Readiness | Admin-only EHR launch configuration check without exposing client secrets |
| SMART Authorization URL | Admin-only authorization URL generation for registered SMART clients without token exchange |
| Terminology Lookup | Authenticated seed coding lookup for common LOINC, SNOMED CT, and ICD-10-CM mappings |
| Patient Export | Current patient downloads or views their own record bundle |
| Doctor Export | Assigned doctor exports a patient bundle only when active consent exists |
| Admin Metrics | Counts exports, consent-backed exports, resources, and active consents |

## Implemented API Surface

Exports:

- `GET /interop/patient/fhir-bundle` - current patient's own bundle
- `GET /interop/doctor/patients/{patient_id}/fhir-bundle` - assigned doctor or admin bundle export, gated by active consent
- `GET /interop/exports/{export_id}/manifest` - role-scoped export manifest without returning the bundle payload

Export profiles:

- `POST /interop/admin/export-profiles` - admin creates a reusable partner export profile
- `GET /interop/admin/export-profiles` - admin lists saved export profiles

Supported export query filters:

- `profile_id={id}` - apply a saved active profile's resource and department scope
- `resource_types=Observation,CareEvent` - comma-separated resource names to include; `Patient` is always included
- `department_id={id}` - include department-scoped records only for the selected department

Direct query filters override the matching saved profile filters for that export request. This allows a hospital admin to save a default partner profile while still supporting a narrower one-off export.

Consent:

- `POST /interop/patient/consents` - current patient grants export consent
- `GET /interop/patient/consents` - current patient reviews consent history
- `POST /interop/patient/consents/{consent_id}/revoke` - current patient revokes consent
- `GET /interop/doctor/patients/{patient_id}/consent-status` - assigned doctor/admin checks active consent status
- `GET /interop/admin/consents` - admin reviews consent records

Metrics:

- `GET /interop/admin/metrics` - admin export counts, consent-backed export counts, active consent counts, and total exported resources

ABDM readiness and consent request preparation:

- `GET /interop/abdm/readiness` - admin-only connector readiness, supported HI types, supported purpose codes, and missing configuration keys without secret values
- `POST /interop/abdm/consent-requests` - assigned doctor/admin prepares an ABDM HIU consent request payload for a local patient and ABHA address; dry-run by default, outbound submission only when `submit=true` and connector configuration is complete
- `POST /interop/abdm/consent-callbacks` - admin-only sandbox callback ingestion for ABDM consent status events; updates linked local consent status, records a PHI-safe `abdm_consent_events` row, and audits the event without storing raw callback payloads

DICOMweb readiness and metadata links:

- `GET /interop/dicomweb/readiness` - admin-only DICOMweb readiness, QIDO-RS/WADO-RS/STOW-RS capability labels, and missing configuration keys without token values
- `GET /interop/dicomweb/studies/{study_instance_uid}/metadata-links` - admin-only metadata/search/store URL shapes for a validated DICOM StudyInstanceUID; returns no image bytes or patient details

SMART on FHIR launch planning:

- `GET /interop/smart/readiness` - admin-only SMART configuration readiness, OAuth endpoint presence, launch capabilities, and scopes without client secret values
- `GET /interop/smart/authorize-url?state={state}&launch={launch}` - admin-only authorization URL generation for a registered SMART client; no token exchange is performed

Terminology:

- `GET /interop/terminology/systems` - authenticated list of supported seed coding systems
- `GET /interop/terminology/lookup?system=loinc&code=8867-4` - authenticated seed terminology lookup returning a FHIR `Coding` shape

## Included Resources

Bundles currently include local records mapped into FHIR-style resource names:

- `Patient`
- `Encounter`
- `Observation`
- `DiagnosticReport`
- `MedicationRequest`
- `Invoice`
- `CareEvent`

## Workflow

1. Hospital workflows create encounters, observations, diagnostics, prescriptions, invoices, and care events.
2. A patient can grant scoped export consent for a stated purpose.
3. An admin can save partner export profiles for common EHR/HIS mapping scopes.
4. A patient can self-export their own bundle at any time.
5. An assigned doctor or admin can export only when active consent exists.
6. The request can use a saved profile and optionally override resource types or department scope.
7. The API builds and validates a current collection bundle from scoped patient data.
8. If generated resources fail FHIR-shape validation, the request returns a controlled `422` before bundle hashing, manifest creation, export logging, or audit recording.
9. The system computes a canonical bundle SHA-256 hash and HMAC-SHA256 manifest signature.
10. The system writes an `interoperability_exports` record and PHI-safe audit event.
11. Admins can record ABDM consent lifecycle callbacks as PHI-safe metadata when running sandbox integration tests.
12. Admins review consent and export metrics for operational oversight.

## ABDM Connector Configuration

The connector reads configuration from environment variables:

- `ABDM_ENABLED` - set `true` only after ABDM onboarding and deployment review.
- `ABDM_ENVIRONMENT` - usually `sandbox` during pilots.
- `ABDM_BASE_URL` and `ABDM_CONSENT_REQUEST_PATH` - deployment-specific HIE-CM/Gateway endpoint values.
- `ABDM_HIU_ID` and optional `ABDM_HIP_ID` - assigned ABDM network identifiers.
- `ABDM_CM_ID` - consent manager suffix, default `sbx`.
- `ABDM_CLIENT_ID`, `ABDM_CLIENT_SECRET`, and `ABDM_ACCESS_TOKEN` - outbound submission credentials; never returned by readiness APIs.
- `ABDM_REQUESTER_NAME`, `ABDM_REQUESTER_IDENTIFIER_TYPE`, `ABDM_REQUESTER_IDENTIFIER_SYSTEM`, and `ABDM_REQUESTER_IDENTIFIER_VALUE` - requester identity values, commonly tied to facility onboarding.

Supported ABDM purpose codes: `CAREMGT`, `BTG`, `PUBHLTH`, `HPAYMT`, `DSRCH`, `PATRQT`.

Default supported HI types: `Prescription`, `DiagnosticReport`, `OPConsultation`, `DischargeSummary`, `ImmunizationRecord`, `HealthDocumentRecord`.

## ABDM Callback Boundary

`POST /interop/abdm/consent-callbacks` is intentionally admin-only in this backend. It is suitable for sandbox readiness testing and controlled connector handoff, not an unauthenticated public ABDM bridge URL. A production bridge endpoint should add deployment-specific gateway authentication, replay protection, IP/network policy, and request signing before accepting external callbacks.

The callback handler stores:

- ABDM request ID and consent artifact ID.
- Consent status and mapped local consent status.
- Supported HI type labels.
- Event timestamp and optional error code.
- SHA-256 hash of normalized callback metadata.

It does not store ABHA addresses, patient names, callback raw bodies, health-information payloads, or ABDM secrets.

## DICOMweb Boundary

`backend/dicomweb.py` prepares DICOMweb readiness metadata and URL shapes for QIDO-RS study search, WADO-RS study metadata retrieval, and STOW-RS store endpoints. It does not call a PACS, retrieve pixel data, store DICOM objects, or expose bearer tokens.

Production PACS integration must be validated against the buyer archive's DICOM conformance statement and access-control model before image exchange.

## SMART on FHIR Boundary

`backend/smart_fhir.py` prepares SMART on FHIR readiness metadata and authorization URLs for EHR launch planning. It does not exchange authorization codes, store refresh tokens, or expose client secrets.

Production EHR launch requires buyer-specific SMART client registration, redirect URI approval, scope review, consent/access-control mapping, and token storage design before enablement.

## Terminology Lookup Boundary

`backend/terminology.py` provides a small PHI-safe seed catalog for common LOINC, SNOMED CT, and ICD-10-CM mappings. It uses canonical FHIR system URIs such as `http://loinc.org`, `http://snomed.info/sct`, and `http://hl7.org/fhir/sid/icd-10-cm`.

This is not a licensed terminology server. Production integrations should validate codes against the hospital or national terminology service before exchange.

## Manifest Integrity

Every bundle export response includes a manifest:

- `bundle_sha256` - canonical hash of the exported bundle payload
- `signature_algorithm` - currently `HMAC-SHA256`
- `signature` - server-generated signature over manifest metadata
- `export_id`, `patient_id`, `requested_by_id`, `consent_id`, and `resource_count`
- `filters` - profile, resource-type, and department filters applied to the export

The manifest is not a regulated digital signature or certification claim. It is a pilot-ready integrity aid for reconciliation, troubleshooting, and partner mapping.

## Roadmap

Next interoperability capabilities:

- Export format versioning.
- Site-specific mapping profiles for hospital HIS/EHR adapters.
- Consent policy templates per hospital or region.
- Public ABDM bridge callback authentication and health-information transfer after partner validation and approval.
- Terminology service adapter for buyer-specific code systems and national catalogs.
- SMART token exchange and launch-context handling after EHR client registration and security review.
