# AI Healthcare System — Route & API Contract Specification Survey

> Authoritative API specification compiled for the Rust (Axum/Tokio) + Bun (ElysiaJS) backend migration.

## 1. Executive Summary & System Overview

- **Total Logical Domains / Routers**: 40 router modules registered in `backend/main.py` + top-level routes
- **Total Unique REST Paths**: 289
- **Total HTTP Operations (Method + Path)**: 305
- **Total Component Schemas (Pydantic / OpenAPI)**: 165
- **WebSocket Endpoints**: 4 route bindings (2 unique handlers: Telemetry Operations Stream, Patient Vitals Stream)
- **Server-Sent Events (SSE) Endpoints**: 2 streaming channels (`/v1/chat/stream`, `/v1/appointments/agent-stream`)
- **Authentication & Security Schemes**: OAuth2 Password Bearer (`/v1/token`), HTTP Bearer JWT tokens (HS256), TOTP 2FA, Multi-Tenant Facility Scoping (`facility_id`), B2B Enterprise Licensing Gate (`enforce_license_tier`)

### Router Domain Breakdown
| Tag / Domain | Operation Count | Primary Prefix | Target Migration Module |
| --- | --- | --- | --- |
| Admin Dashboard | 40 | `/v1/admin` | `rust_gateway::routes::admin_dashboard` |
| Interoperability | 33 | `/v1/interop` | `rust_gateway::routes::interoperability` |
| Unified Data Platform | 22 | `/api` | `rust_gateway::routes::unified_data_platform` |
| Prediction | 21 | `/v1/admin` | `rust_gateway::routes::prediction` |
| Hospital Operations | 17 | `/v1/hospital` | `rust_gateway::routes::hospital_operations` |
| Auth | 11 | `/v1/signup` | `rust_gateway::routes::auth` |
| Billing | 11 | `/v1/billing` | `rust_gateway::routes::billing` |
| Pharmacy | 10 | `/v1/pharmacy` | `rust_gateway::routes::pharmacy` |
| Appointments | 10 | `/v1/appointments` | `rust_gateway::routes::appointments` |
| Top-Level & System | 10 | `/` | `rust_gateway::routes::top_level_&_system` |
| Diagnostics | 9 | `/v1/diagnostics` | `rust_gateway::routes::diagnostics` |
| Chat | 8 | `/v1/chat` | `rust_gateway::routes::chat` |
| Nursing | 7 | `/v1/nursing` | `rust_gateway::routes::nursing` |
| Monitoring | 6 | `/v1/monitoring` | `rust_gateway::routes::monitoring` |
| Discharge | 6 | `/v1/discharge` | `rust_gateway::routes::discharge` |
| Care Events | 6 | `/v1/events` | `rust_gateway::routes::care_events` |
| Telemetry | 6 | `/v1/telemetry` | `rust_gateway::routes::telemetry` |
| FHIR R4 | 6 | `/v1/fhir` | `rust_gateway::routes::fhir_r4` |
| Lakehouse Data Engineering | 6 | `/v1/lakehouse` | `rust_gateway::routes::lakehouse_data_engineering` |
| SMART on FHIR | 5 | `/v1/smart` | `rust_gateway::routes::smart_on_fhir` |
| Recommendation Engine | 5 | `/v1/recommendations` | `rust_gateway::routes::recommendation_engine` |
| Four-Eye Clinical Governance & AI Safety | 5 | `/v1/governance` | `rust_gateway::routes::four_eye_clinical_governance_&_ai_safety` |
| Ollama Models | 4 | `/v1/ai` | `rust_gateway::routes::ollama_models` |
| Longitudinal Predictions | 4 | `/v1/predict` | `rust_gateway::routes::longitudinal_predictions` |
| Federated Learning | 4 | `/v1/federated` | `rust_gateway::routes::federated_learning` |
| Clinical Intelligence | 4 | `/v1/intelligence` | `rust_gateway::routes::clinical_intelligence` |
| ABDM Sandbox | 4 | `/v1/abdm` | `rust_gateway::routes::abdm_sandbox` |
| Streaming Chat | 3 | `/v1/chat` | `rust_gateway::routes::streaming_chat` |
| DICOMweb PACS | 3 | `/v1/dicomweb` | `rust_gateway::routes::dicomweb_pacs` |
| i18n Audio | 3 | `/v1/audio` | `rust_gateway::routes::i18n_audio` |
| Peak Healthcare Intelligence | 3 | `/v1/digital-twin` | `rust_gateway::routes::peak_healthcare_intelligence` |
| Reports | 2 | `/v1/analyze` | `rust_gateway::routes::reports` |
| Payments | 2 | `/v1/payments` | `rust_gateway::routes::payments` |
| Consent | 2 | `/v1/consent` | `rust_gateway::routes::consent` |
| FHIR Compression | 2 | `/v1/fhir` | `rust_gateway::routes::fhir_compression` |
| Multi-Cloud Pipeline Mesh | 2 | `/v1/mesh` | `rust_gateway::routes::multi_cloud_pipeline_mesh` |
| Explanation | 1 | `/v1/explain` | `rust_gateway::routes::explanation` |
| Sales Readiness | 1 | `/v1/admin` | `rust_gateway::routes::sales_readiness` |
| Demo Readiness | 1 | `/v1/demo-readiness` | `rust_gateway::routes::demo_readiness` |

---
## 2. Exhaustive Domain & Router Catalog

### 2.1 Admin Dashboard (40 Endpoints)

| Method | Full Route Path | Summary / Description | Auth & Security | Request Body / Params | Response Codes & Schema |
| --- | --- | --- | --- | --- | --- |
| `POST` | `/v1/admin/agents/auto-call` | Trigger Auto Calling Agent | OAuth2PasswordBearer | `alert_details` (query:string:opt), `staff_directory` (query:string:opt) | `200`: `json`<br>`422`: `HTTPValidationError` |
| `POST` | `/v1/admin/agents/auto-fix` | Trigger Auto Fixing Agent | OAuth2PasswordBearer | `error_logs` (query:string:opt), `health_signals` (query:string:opt) | `200`: `json`<br>`422`: `HTTPValidationError` |
| `POST` | `/v1/admin/agents/billing-audit` | Trigger Billing Agent Audit | OAuth2PasswordBearer | `soap_note` (query:string:req) | `200`: `json`<br>`422`: `HTTPValidationError` |
| `POST` | `/v1/admin/agents/discharge-summary` | Trigger Discharge Agent Summary | OAuth2PasswordBearer | `patient_id` (query:integer:req) | `200`: `json`<br>`422`: `HTTPValidationError` |
| `POST` | `/v1/admin/agents/langgraph-triage` | Trigger Langgraph Triage | OAuth2PasswordBearer | `symptoms` (query:string:req), `patient_id` (query:integer:opt) | `200`: `json`<br>`422`: `HTTPValidationError` |
| `POST` | `/v1/admin/agents/maf-billing-audit` | Trigger Maf Billing Agent Audit | OAuth2PasswordBearer | `soap_note` (query:string:req) | `200`: `json`<br>`422`: `HTTPValidationError` |
| `POST` | `/v1/admin/agents/maf-handoff-audit` | Trigger Maf Handoff Agent Audit | OAuth2PasswordBearer | `soap_note` (query:string:req) | `200`: `json`<br>`422`: `HTTPValidationError` |
| `POST` | `/v1/admin/agents/nursing-handoff` | Trigger Nursing Agent Handoff | OAuth2PasswordBearer | `patient_id` (query:integer:req) | `200`: `json`<br>`422`: `HTTPValidationError` |
| `POST` | `/v1/admin/agents/security-patch` | Trigger Security Patch Agent | OAuth2PasswordBearer | `dependencies` (query:string:opt), `env_config` (query:string:opt) | `200`: `json`<br>`422`: `HTTPValidationError` |
| `POST` | `/v1/admin/agents/wellness-advisory` | Trigger Wellness Agent | OAuth2PasswordBearer | `patient_data` (query:string:opt) | `200`: `json`<br>`422`: `HTTPValidationError` |
| `GET` | `/v1/admin/ai-functions` | Get Ai Function Registry | OAuth2PasswordBearer | None | `200`: `object` |
| `GET` | `/v1/admin/analytics/report` | Get Analytics Report | OAuth2PasswordBearer | None | `200`: `object` |
| `GET` | `/v1/admin/attribution-drift` | Get Attribution Drift Report | OAuth2PasswordBearer | None | `200`: `object` |
| `GET` | `/v1/admin/audit-logs` | Get Audit Logs | OAuth2PasswordBearer | `skip` (query:integer:opt), `limit` (query:integer:opt), `action` (query:any:opt), `target_user_id` (query:any:opt) | `200`: `array`<br>`422`: `HTTPValidationError` |
| `GET` | `/v1/admin/audit-logs/export` | Export Audit Logs Csv | OAuth2PasswordBearer | `action` (query:any:opt), `target_user_id` (query:any:opt) | `200`: `json`<br>`422`: `HTTPValidationError` |
| `GET` | `/v1/admin/backup-readiness` | Get Backup Readiness Report | OAuth2PasswordBearer | None | `200`: `object` |
| `POST` | `/v1/admin/backups/execute` | Execute Database Backup | OAuth2PasswordBearer | None | `200`: `object` |
| `GET` | `/v1/admin/breaches` | List Breaches | OAuth2PasswordBearer | `include_resolved` (query:boolean:opt) | `200`: `json`<br>`422`: `HTTPValidationError` |
| `POST` | `/v1/admin/breaches/report` | Report Breach | OAuth2PasswordBearer | `description` (query:string:req), `severity` (query:string:opt), `affected_records` (query:integer:opt), `phi_involved` (query:boolean:opt) | `200`: `json`<br>`422`: `HTTPValidationError` |
| `GET` | `/v1/admin/compliance/hipaa` | Hipaa Compliance Check | OAuth2PasswordBearer | None | `200`: `json` |
| `GET` | `/v1/admin/data-quality` | Get Data Quality Report | OAuth2PasswordBearer | None | `200`: `object` |
| `POST` | `/v1/admin/federated-sim` | Run Federated Simulation | OAuth2PasswordBearer | `epochs` (query:integer:opt), `epsilon` (query:number:opt) | `200`: `object`<br>`422`: `HTTPValidationError` |
| `GET` | `/v1/admin/incident-readiness` | Get Incident Readiness Report | OAuth2PasswordBearer | None | `200`: `object` |
| `POST` | `/v1/admin/maintenance` | Trigger System Maintenance | OAuth2PasswordBearer | None | `200`: `json` |
| `GET` | `/v1/admin/model-cards` | Get Model Cards | OAuth2PasswordBearer | None | `200`: `object` |
| `GET` | `/v1/admin/operational-health` | Get Operational Health Report | OAuth2PasswordBearer | None | `200`: `object` |
| `GET` | `/v1/admin/patients` | Get Admin Patients | OAuth2PasswordBearer | `skip` (query:integer:opt), `limit` (query:integer:opt) | `200`: `array`<br>`422`: `HTTPValidationError` |
| `GET` | `/v1/admin/patients/{patient_id}` | Get Admin Patient Profile | OAuth2PasswordBearer | `patient_id` (path:integer:req) | `200`: `object`<br>`422`: `HTTPValidationError` |
| `GET` | `/v1/admin/privacy/deletion-plan/{patient_id}` | Get Patient Deletion Plan | OAuth2PasswordBearer | `patient_id` (path:integer:req) | `200`: `object`<br>`422`: `HTTPValidationError` |
| `POST` | `/v1/admin/privacy/execute-deletion/{patient_id}` | Execute Patient Deletion | OAuth2PasswordBearer | `patient_id` (path:integer:req) | `200`: `object`<br>`422`: `HTTPValidationError` |
| `GET` | `/v1/admin/retention-readiness` | Get Retention Readiness Report | OAuth2PasswordBearer | None | `200`: `object` |
| `POST` | `/v1/admin/retention/execute-cleanup` | Execute Retention Cleanup | OAuth2PasswordBearer | None | `200`: `object` |
| `GET` | `/v1/admin/security-assurance` | Get Security Assurance Report | OAuth2PasswordBearer | None | `200`: `object` |
| `DELETE` | `/v1/admin/semantic-cache` | Clear Semantic Cache | OAuth2PasswordBearer | None | `200`: `object` |
| `GET` | `/v1/admin/semantic-cache` | Get Semantic Cache Stats | OAuth2PasswordBearer | None | `200`: `object` |
| `GET` | `/v1/admin/stats` | Get Admin Stats | OAuth2PasswordBearer | None | `200`: `object` |
| `GET` | `/v1/admin/users` | Get Recent Users | OAuth2PasswordBearer | `skip` (query:integer:opt), `limit` (query:integer:opt) | `200`: `json`<br>`422`: `HTTPValidationError` |
| `DELETE` | `/v1/admin/users/{user_id}` | Delete User | OAuth2PasswordBearer | `user_id` (path:integer:req) | `200`: `json`<br>`422`: `HTTPValidationError` |
| `PUT` | `/v1/admin/users/{user_id}/facility` | Assign User Facility | OAuth2PasswordBearer | `user_id` (path:integer:req), `facility_id` (query:integer:req) | `200`: `json`<br>`422`: `HTTPValidationError` |
| `PUT` | `/v1/admin/users/{user_id}/role` | Update User Role | OAuth2PasswordBearer | `user_id` (path:integer:req), `role` (query:string:req) | `200`: `json`<br>`422`: `HTTPValidationError` |

### 2.2 Interoperability (33 Endpoints)

| Method | Full Route Path | Summary / Description | Auth & Security | Request Body / Params | Response Codes & Schema |
| --- | --- | --- | --- | --- | --- |
| `POST` | `/v1/interop/abdm/consent-callbacks` | Record Abdm Consent Callback | OAuth2PasswordBearer | Body: `ABDMConsentCallbackCreate` | `201`: `object`<br>`422`: `HTTPValidationError` |
| `POST` | `/v1/interop/abdm/consent-requests` | Prepare Abdm Consent Request | OAuth2PasswordBearer | Body: `ABDMConsentRequestCreate` | `200`: `object`<br>`422`: `HTTPValidationError` |
| `POST` | `/v1/interop/abdm/link` | Link Abha Address | OAuth2PasswordBearer | Body: `object` | `201`: `json`<br>`422`: `HTTPValidationError` |
| `GET` | `/v1/interop/abdm/readiness` | Get Abdm Readiness | OAuth2PasswordBearer | None | `200`: `object` |
| `GET` | `/v1/interop/admin/consents` | List Admin Interoperability Consents | OAuth2PasswordBearer | `patient_id` (query:any:opt) | `200`: `array`<br>`422`: `HTTPValidationError` |
| `GET` | `/v1/interop/admin/export-profiles` | List Admin Export Profiles | OAuth2PasswordBearer | None | `200`: `array` |
| `POST` | `/v1/interop/admin/export-profiles` | Create Admin Export Profile | OAuth2PasswordBearer | Body: `InteroperabilityExportProfileCreate` | `200`: `object`<br>`422`: `HTTPValidationError` |
| `GET` | `/v1/interop/admin/metrics` | Get Interoperability Metrics | OAuth2PasswordBearer | None | `200`: `object` |
| `GET` | `/v1/interop/ai/governance-ledger` | Get Ai Governance Ledger | OAuth2PasswordBearer | None | `200`: `object` |
| `POST` | `/v1/interop/ai/override-audit` | Record Ai Override Audit | OAuth2PasswordBearer | Body: `ClinicianOverrideRequest` | `201`: `object`<br>`422`: `HTTPValidationError` |
| `GET` | `/v1/interop/consents` | List Consents Alias | OAuth2PasswordBearer | None | `200`: `array` |
| `POST` | `/v1/interop/consents` | Grant Consent Alias | OAuth2PasswordBearer | Body: `InteroperabilityConsentCreate` | `200`: `object`<br>`422`: `HTTPValidationError` |
| `PUT` | `/v1/interop/consents/{consent_id}/revoke` | Revoke Consent Alias Put | OAuth2PasswordBearer | `consent_id` (path:integer:req) | `200`: `object`<br>`422`: `HTTPValidationError` |
| `GET` | `/v1/interop/dicomweb/readiness` | Get Dicomweb Readiness | OAuth2PasswordBearer | None | `200`: `object` |
| `GET` | `/v1/interop/dicomweb/studies/{study_instance_uid}/metadata-links` | Get Dicomweb Study Metadata Links | OAuth2PasswordBearer | `study_instance_uid` (path:string:req) | `200`: `object`<br>`422`: `HTTPValidationError` |
| `GET` | `/v1/interop/doctor/patients/{patient_id}/consent-status` | Get Doctor Patient Consent Status | OAuth2PasswordBearer | `patient_id` (path:integer:req) | `200`: `object`<br>`422`: `HTTPValidationError` |
| `GET` | `/v1/interop/doctor/patients/{patient_id}/fhir-bundle` | Export Doctor Patient Bundle | OAuth2PasswordBearer | `patient_id` (path:integer:req), `resource_types` (query:any:opt), `department_id` (query:any:opt), `profile_id` (query:any:opt) | `200`: `object`<br>`422`: `HTTPValidationError` |
| `GET` | `/v1/interop/ehr/providers` | List Ehr Providers | OAuth2PasswordBearer | None | `200`: `json` |
| `POST` | `/v1/interop/ehr/sync/{provider_id}` | Sync Ehr Patient Data | OAuth2PasswordBearer | `provider_id` (path:string:req)<br>Body: `object` | `200`: `json`<br>`422`: `HTTPValidationError` |
| `GET` | `/v1/interop/export/patient` | Export Patient Alias | OAuth2PasswordBearer | None | `200`: `object` |
| `POST` | `/v1/interop/export/patient` | Export Patient Alias | OAuth2PasswordBearer | None | `200`: `object` |
| `GET` | `/v1/interop/exports/{export_id}/manifest` | Get Export Manifest | OAuth2PasswordBearer | `export_id` (path:integer:req) | `200`: `object`<br>`422`: `HTTPValidationError` |
| `GET` | `/v1/interop/external-records/{patient_id}` | Get External Records | OAuth2PasswordBearer | `patient_id` (path:integer:req) | `200`: `object`<br>`422`: `HTTPValidationError` |
| `GET` | `/v1/interop/health-passport/{patient_id}` | Get Health Passport | OAuth2PasswordBearer | `patient_id` (path:integer:req) | `200`: `object`<br>`422`: `HTTPValidationError` |
| `GET` | `/v1/interop/patient/consents` | List Patient Interoperability Consents | OAuth2PasswordBearer | None | `200`: `array` |
| `POST` | `/v1/interop/patient/consents` | Grant Patient Interoperability Consent | OAuth2PasswordBearer | Body: `InteroperabilityConsentCreate` | `201`: `object`<br>`422`: `HTTPValidationError` |
| `POST` | `/v1/interop/patient/consents/{consent_id}/revoke` | Revoke Patient Interoperability Consent | OAuth2PasswordBearer | `consent_id` (path:integer:req) | `200`: `object`<br>`422`: `HTTPValidationError` |
| `GET` | `/v1/interop/patient/fhir-bundle` | Export Patient Bundle | OAuth2PasswordBearer | `resource_types` (query:any:opt), `department_id` (query:any:opt), `profile_id` (query:any:opt) | `200`: `object`<br>`422`: `HTTPValidationError` |
| `GET` | `/v1/interop/smart/authorize-url` | Get Smart Authorization Url | OAuth2PasswordBearer | `state` (query:any:opt), `launch` (query:any:opt), `scope` (query:any:opt) | `200`: `object`<br>`422`: `HTTPValidationError` |
| `GET` | `/v1/interop/smart/readiness` | Get Smart Fhir Readiness | OAuth2PasswordBearer | None | `200`: `object` |
| `GET` | `/v1/interop/terminology/lookup` | Lookup Terminology Code | OAuth2PasswordBearer | `system` (query:string:req), `code` (query:string:req) | `200`: `object`<br>`422`: `HTTPValidationError` |
| `POST` | `/v1/interop/terminology/search` | Search Terminology Concepts | OAuth2PasswordBearer | Body: `TerminologySearchRequest` | `200`: `object`<br>`422`: `HTTPValidationError` |
| `GET` | `/v1/interop/terminology/systems` | List Terminology Systems | OAuth2PasswordBearer | None | `200`: `object` |

### 2.3 Unified Data Platform (22 Endpoints)

| Method | Full Route Path | Summary / Description | Auth & Security | Request Body / Params | Response Codes & Schema |
| --- | --- | --- | --- | --- | --- |
| `GET` | `/api/v1/data-platform/agents/benchmark/run` | Run Agent Performance Benchmark | Public / None | None | `200`: `object` |
| `POST` | `/api/v1/data-platform/agents/cost-analyzer/analyze` | Analyze Patient Cost | Public / None | Body: `object` | `200`: `object`<br>`422`: `HTTPValidationError` |
| `POST` | `/api/v1/data-platform/agents/entity-resolution/resolve` | Resolve Patient Entity | Public / None | Body: `object` | `200`: `object`<br>`422`: `HTTPValidationError` |
| `POST` | `/api/v1/data-platform/agents/fraud-detection/analyze` | Analyze Claim Fraud | Public / None | Body: `object` | `200`: `object`<br>`422`: `HTTPValidationError` |
| `POST` | `/api/v1/data-platform/agents/future-forecast/predict` | Predict Hospital Forecast | Public / None | Body: `object` | `200`: `object`<br>`422`: `HTTPValidationError` |
| `POST` | `/api/v1/data-platform/agents/governed-execute` | Execute Governed Agent | Public / None | Body: `object` | `200`: `object`<br>`422`: `HTTPValidationError` |
| `GET` | `/api/v1/data-platform/agents/lineage` | Get Agent Data Lineage | Public / None | None | `200`: `object` |
| `POST` | `/api/v1/data-platform/agents/mesh/consensus-debate` | Run Agent Consensus Debate | Public / None | Body: `object` | `200`: `object`<br>`422`: `HTTPValidationError` |
| `POST` | `/api/v1/data-platform/agents/mesh/dag-orchestrate` | Orchestrate Dag Plan | Public / None | Body: `object` | `200`: `object`<br>`422`: `HTTPValidationError` |
| `POST` | `/api/v1/data-platform/agents/mesh/execute-react-goal` | Execute React Reflexion Goal | Public / None | Body: `object` | `200`: `object`<br>`422`: `HTTPValidationError` |
| `POST` | `/api/v1/data-platform/agents/plan-and-execute` | Plan And Execute Agent Goal | Public / None | Body: `PlanExecuteRequest` | `200`: `object`<br>`422`: `HTTPValidationError` |
| `POST` | `/api/v1/data-platform/agents/prior-auth/process` | Process Prior Auth Request | Public / None | Body: `object` | `200`: `object`<br>`422`: `HTTPValidationError` |
| `POST` | `/api/v1/data-platform/agents/route` | Route Agent Task | Public / None | Body: `AgentRouteRequest` | `200`: `object`<br>`422`: `HTTPValidationError` |
| `POST` | `/api/v1/data-platform/agents/rpm-adherence/evaluate` | Evaluate Rpm Adherence | Public / None | Body: `object` | `200`: `object`<br>`422`: `HTTPValidationError` |
| `POST` | `/api/v1/data-platform/agents/sepsis/evaluate` | Evaluate Icu Sepsis Risk | Public / None | Body: `object` | `200`: `object`<br>`422`: `HTTPValidationError` |
| `POST` | `/api/v1/data-platform/agents/surgical-or/optimize` | Optimize Surgical Or Schedule | Public / None | Body: `object` | `200`: `object`<br>`422`: `HTTPValidationError` |
| `POST` | `/api/v1/data-platform/agents/trial-matching/match` | Match Clinical Trials | Public / None | Body: `object` | `200`: `object`<br>`422`: `HTTPValidationError` |
| `GET` | `/api/v1/data-platform/apps/list` | List Data Apps | Public / None | None | `200`: `object` |
| `POST` | `/api/v1/data-platform/bi/ask` | Ask Agentic Bi | Public / None | Body: `BIAskRequest` | `200`: `object`<br>`422`: `HTTPValidationError` |
| `GET` | `/api/v1/data-platform/catalog/search` | Search Catalog | Public / None | `query` (query:string:req), `asset_type` (query:any:opt) | `200`: `object`<br>`422`: `HTTPValidationError` |
| `POST` | `/api/v1/data-platform/spark/variant-shred` | Shred Variant Json | Public / None | Body: `VariantShredRequest` | `200`: `object`<br>`422`: `HTTPValidationError` |
| `POST` | `/api/v1/data-platform/sql/execute` | Execute Lakehouse Sql | Public / None | Body: `SQLExecuteRequest` | `200`: `object`<br>`422`: `HTTPValidationError` |

### 2.4 Prediction (21 Endpoints)

| Method | Full Route Path | Summary / Description | Auth & Security | Request Body / Params | Response Codes & Schema |
| --- | --- | --- | --- | --- | --- |
| `GET` | `/v1/admin/models/health` | Models Health Check | OAuth2PasswordBearer | None | `200`: `json` |
| `POST` | `/v1/admin/reload_models` | Reload Models | OAuth2PasswordBearer | None | `200`: `json` |
| `GET` | `/v1/predict/advisory-board/{patient_id}` | Get Advisory Board | OAuth2PasswordBearer | `patient_id` (path:integer:req) | `200`: `object`<br>`422`: `HTTPValidationError` |
| `GET` | `/v1/predict/clinical-trials/{patient_id}` | Match Clinical Trials | OAuth2PasswordBearer | `patient_id` (path:integer:req) | `200`: `json`<br>`422`: `HTTPValidationError` |
| `GET` | `/v1/predict/consensus/{patient_id}` | Get Clinical Consensus | OAuth2PasswordBearer | `patient_id` (path:integer:req) | `200`: `json`<br>`422`: `HTTPValidationError` |
| `POST` | `/v1/predict/counterfactual/{patient_id}` | Counterfactual Recourse | OAuth2PasswordBearer | `patient_id` (path:integer:req)<br>Body: `CounterfactualRequest` | `200`: `json`<br>`422`: `HTTPValidationError` |
| `POST` | `/v1/predict/diabetes` | Predict Diabetes | OAuth2PasswordBearer | Body: `DiabetesInput` | `200`: `object`<br>`422`: `HTTPValidationError` |
| `POST` | `/v1/predict/explain-text/{model_name}` | Get Patient Explanation Endpoint | OAuth2PasswordBearer | `model_name` (path:string:req)<br>Body: `backend__prediction__ExplanationRequest` | `200`: `object`<br>`422`: `HTTPValidationError` |
| `POST` | `/v1/predict/explain/diabetes` | Explain Diabetes | OAuth2PasswordBearer | Body: `DiabetesInput` | `200`: `json`<br>`422`: `HTTPValidationError` |
| `POST` | `/v1/predict/explain/heart` | Explain Heart | OAuth2PasswordBearer | Body: `HeartInput` | `200`: `json`<br>`422`: `HTTPValidationError` |
| `POST` | `/v1/predict/explain/liver` | Explain Liver | OAuth2PasswordBearer | Body: `LiverInput` | `200`: `json`<br>`422`: `HTTPValidationError` |
| `POST` | `/v1/predict/heart` | Predict Heart | OAuth2PasswordBearer | Body: `HeartInput` | `200`: `object`<br>`422`: `HTTPValidationError` |
| `POST` | `/v1/predict/kidney` | Predict Kidney | OAuth2PasswordBearer | Body: `KidneyInput` | `200`: `object`<br>`422`: `HTTPValidationError` |
| `POST` | `/v1/predict/liver` | Predict Liver | OAuth2PasswordBearer | Body: `LiverInput` | `200`: `object`<br>`422`: `HTTPValidationError` |
| `POST` | `/v1/predict/lungs` | Predict Lungs | OAuth2PasswordBearer | Body: `LungInput` | `200`: `object`<br>`422`: `HTTPValidationError` |
| `POST` | `/v1/predict/multi-organ` | Predict Multi Organ | OAuth2PasswordBearer | Body: `MultiOrganInput` | `200`: `object`<br>`422`: `HTTPValidationError` |
| `GET` | `/v1/predict/organ_health/{patient_id}` | Predict Organ Health | OAuth2PasswordBearer | `patient_id` (path:integer:req) | `200`: `object`<br>`422`: `HTTPValidationError` |
| `POST` | `/v1/predict/reviews` | Record Prediction Review | OAuth2PasswordBearer | Body: `PredictionReviewCreate` | `201`: `object`<br>`422`: `HTTPValidationError` |
| `POST` | `/v1/predict/scribe/commit` | Commit Scribe Soap | OAuth2PasswordBearer | Body: `ScribeCommitRequest` | `200`: `json`<br>`422`: `HTTPValidationError` |
| `POST` | `/v1/predict/scribe/{patient_id}` | Generate Scribe Soap | OAuth2PasswordBearer | `patient_id` (path:integer:req)<br>Body: `ScribeRequest` | `200`: `json`<br>`422`: `HTTPValidationError` |
| `POST` | `/v1/predict/stroke` | Predict Stroke | OAuth2PasswordBearer | Body: `StrokeInput` | `200`: `object`<br>`422`: `HTTPValidationError` |

### 2.5 Hospital Operations (17 Endpoints)

| Method | Full Route Path | Summary / Description | Auth & Security | Request Body / Params | Response Codes & Schema |
| --- | --- | --- | --- | --- | --- |
| `GET` | `/v1/hospital/admin/operations` | Get Admin Operations | OAuth2PasswordBearer | None | `200`: `object` |
| `POST` | `/v1/hospital/admissions` | Create Admission | OAuth2PasswordBearer | Body: `AdmissionCreate` | `200`: `AdmissionResponse`<br>`422`: `HTTPValidationError` |
| `GET` | `/v1/hospital/beds` | List Beds | OAuth2PasswordBearer | `status` (query:any:opt) | `200`: `List[BedResponse]`<br>`422`: `HTTPValidationError` |
| `POST` | `/v1/hospital/beds` | Create Bed | OAuth2PasswordBearer | Body: `BedCreate` | `200`: `BedResponse`<br>`422`: `HTTPValidationError` |
| `PATCH` | `/v1/hospital/beds/{bed_id}/status` | Update Bed Status | OAuth2PasswordBearer | `bed_id` (path:integer:req)<br>Body: `BedStatusUpdate` | `200`: `BedResponse`<br>`422`: `HTTPValidationError` |
| `GET` | `/v1/hospital/departments` | List Departments | OAuth2PasswordBearer | None | `200`: `List[DepartmentResponse]` |
| `POST` | `/v1/hospital/departments` | Create Department | OAuth2PasswordBearer | Body: `DepartmentCreate` | `200`: `DepartmentResponse`<br>`422`: `HTTPValidationError` |
| `POST` | `/v1/hospital/dicom/upload` | Upload Dicom Study | OAuth2PasswordBearer | Body: `object` | `201`: `json`<br>`422`: `HTTPValidationError` |
| `POST` | `/v1/hospital/dictation/soap` | Process Soap Dictation | OAuth2PasswordBearer | Body: `object` | `200`: `json`<br>`422`: `HTTPValidationError` |
| `GET` | `/v1/hospital/doctor/insights` | Get Doctor Insights | OAuth2PasswordBearer | None | `200`: `object` |
| `GET` | `/v1/hospital/doctor/patients` | Get Doctor Patients | OAuth2PasswordBearer | None | `200`: `array` |
| `POST` | `/v1/hospital/encounters` | Create Encounter | OAuth2PasswordBearer | Body: `EncounterCreate` | `200`: `EncounterResponse`<br>`422`: `HTTPValidationError` |
| `GET` | `/v1/hospital/facilities` | List Facilities | OAuth2PasswordBearer | None | `200`: `List[FacilityResponse]` |
| `POST` | `/v1/hospital/facilities` | Create Facility | OAuth2PasswordBearer | Body: `FacilityCreate` | `200`: `FacilityResponse`<br>`422`: `HTTPValidationError` |
| `POST` | `/v1/hospital/orders` | Create Order | OAuth2PasswordBearer | Body: `ClinicalOrderCreate` | `200`: `ClinicalOrderResponse`<br>`422`: `HTTPValidationError` |
| `GET` | `/v1/hospital/patient/timeline` | Get Patient Timeline | OAuth2PasswordBearer | None | `200`: `PatientTimelineResponse` |
| `GET` | `/v1/hospital/triage-queue` | Get Triage Queue | OAuth2PasswordBearer | None | `200`: `object` |

### 2.6 Auth (11 Endpoints)

| Method | Full Route Path | Summary / Description | Auth & Security | Request Body / Params | Response Codes & Schema |
| --- | --- | --- | --- | --- | --- |
| `POST` | `/v1/2fa/enable` | Enable 2Fa | OAuth2PasswordBearer | Body: `TOTPVerifyRequest` | `200`: `json`<br>`422`: `HTTPValidationError` |
| `POST` | `/v1/2fa/setup` | Setup 2Fa | OAuth2PasswordBearer | None | `200`: `TOTPSetupResponse` |
| `POST` | `/v1/forgot-password` | Forgot Password | Public / None | Body: `ForgotPasswordRequest` | `200`: `object`<br>`422`: `HTTPValidationError` |
| `DELETE` | `/v1/me` | Delete Account | OAuth2PasswordBearer | None | `204`: `any` |
| `GET` | `/v1/profile` | Get User Profile | OAuth2PasswordBearer | None | `200`: `object` |
| `PUT` | `/v1/profile` | Update User Profile | OAuth2PasswordBearer | Body: `UserProfileUpdate` | `200`: `object`<br>`422`: `HTTPValidationError` |
| `POST` | `/v1/reset-password` | Reset Password | Public / None | Body: `ResetPasswordRequest` | `200`: `object`<br>`422`: `HTTPValidationError` |
| `POST` | `/v1/signup` | Signup | Public / None | Body: `UserCreate` | `200`: `UserResponse`<br>`422`: `HTTPValidationError` |
| `POST` | `/v1/token` | Login For Access Token | Public / None | Body: `Body_login_for_access_token_v1_token_post` | `200`: `Token`<br>`422`: `HTTPValidationError` |
| `GET` | `/v1/users` | Get All Users | OAuth2PasswordBearer | None | `200`: `List[UserResponse]` |
| `GET` | `/v1/users/{user_id}/full` | Get User Full Details | OAuth2PasswordBearer | `user_id` (path:integer:req) | `200`: `UserFullResponse`<br>`422`: `HTTPValidationError` |

### 2.7 Billing (11 Endpoints)

| Method | Full Route Path | Summary / Description | Auth & Security | Request Body / Params | Response Codes & Schema |
| --- | --- | --- | --- | --- | --- |
| `GET` | `/v1/billing/admin/invoices` | List Invoices | OAuth2PasswordBearer | None | `200`: `List[InvoiceResponse]` |
| `GET` | `/v1/billing/admin/metrics` | Get Billing Metrics | OAuth2PasswordBearer | None | `200`: `object` |
| `POST` | `/v1/billing/claims/submit` | Submit Insurance Claim | OAuth2PasswordBearer | Body: `object` | `201`: `json`<br>`422`: `HTTPValidationError` |
| `GET` | `/v1/billing/estimate` | Get Procedure Cost Estimate | OAuth2PasswordBearer | `procedure_type` (query:string:req), `insurance_provider` (query:any:opt), `region` (query:string:opt) | `200`: `object`<br>`422`: `HTTPValidationError` |
| `POST` | `/v1/billing/invoices` | Create Invoice | OAuth2PasswordBearer | Body: `InvoiceCreate` | `200`: `InvoiceResponse`<br>`422`: `HTTPValidationError` |
| `POST` | `/v1/billing/invoices/{invoice_id}/audit` | Audit Invoice Denial Risk | OAuth2PasswordBearer | `invoice_id` (path:integer:req) | `200`: `json`<br>`422`: `HTTPValidationError` |
| `POST` | `/v1/billing/invoices/{invoice_id}/payments` | Record Invoice Payment | OAuth2PasswordBearer | `invoice_id` (path:integer:req)<br>Body: `BillingPaymentCreate` | `200`: `object`<br>`422`: `HTTPValidationError` |
| `GET` | `/v1/billing/patient/invoices` | Get Patient Invoices | OAuth2PasswordBearer | None | `200`: `List[InvoiceResponse]` |
| `GET` | `/v1/billing/services` | List Billable Services | OAuth2PasswordBearer | None | `200`: `List[BillableServiceResponse]` |
| `POST` | `/v1/billing/services` | Create Billable Service | OAuth2PasswordBearer | Body: `BillableServiceCreate` | `200`: `BillableServiceResponse`<br>`422`: `HTTPValidationError` |
| `POST` | `/v1/billing/soap-audit` | Audit Soap Note Denial | OAuth2PasswordBearer | Body: `object` | `200`: `json`<br>`422`: `HTTPValidationError` |

### 2.8 Pharmacy (10 Endpoints)

| Method | Full Route Path | Summary / Description | Auth & Security | Request Body / Params | Response Codes & Schema |
| --- | --- | --- | --- | --- | --- |
| `GET` | `/v1/pharmacy/admin/metrics` | Get Pharmacy Metrics | OAuth2PasswordBearer | None | `200`: `object` |
| `POST` | `/v1/pharmacy/check-safety` | Check Prescription Safety | OAuth2PasswordBearer | Body: `DrugSafetyCheckRequest` | `200`: `json`<br>`422`: `HTTPValidationError` |
| `GET` | `/v1/pharmacy/compare-pricing` | Compare Medication Pricing | OAuth2PasswordBearer | `medication_name` (query:string:req) | `200`: `object`<br>`422`: `HTTPValidationError` |
| `GET` | `/v1/pharmacy/doctor/patients/{patient_id}/prescriptions` | Get Doctor Patient Prescriptions | OAuth2PasswordBearer | `patient_id` (path:integer:req) | `200`: `object`<br>`422`: `HTTPValidationError` |
| `GET` | `/v1/pharmacy/generic-substitute` | Get Generic Substitution | OAuth2PasswordBearer | `branded_name` (query:string:req) | `200`: `object`<br>`422`: `HTTPValidationError` |
| `GET` | `/v1/pharmacy/inventory` | List Inventory | OAuth2PasswordBearer | None | `200`: `List[MedicationInventoryResponse]` |
| `POST` | `/v1/pharmacy/inventory` | Create Inventory Item | OAuth2PasswordBearer | Body: `MedicationInventoryCreate` | `200`: `MedicationInventoryResponse`<br>`422`: `HTTPValidationError` |
| `GET` | `/v1/pharmacy/patient/prescriptions` | Get Patient Prescriptions | OAuth2PasswordBearer | None | `200`: `List[PrescriptionResponse]` |
| `POST` | `/v1/pharmacy/prescriptions` | Create Prescription | OAuth2PasswordBearer | Body: `PrescriptionCreate` | `200`: `PrescriptionResponse`<br>`422`: `HTTPValidationError` |
| `POST` | `/v1/pharmacy/prescriptions/{prescription_id}/dispense` | Dispense Prescription | OAuth2PasswordBearer | `prescription_id` (path:integer:req)<br>Body: `DispensePrescriptionCreate` | `200`: `PrescriptionResponse`<br>`422`: `HTTPValidationError` |

### 2.9 Appointments (10 Endpoints)

| Method | Full Route Path | Summary / Description | Auth & Security | Request Body / Params | Response Codes & Schema |
| --- | --- | --- | --- | --- | --- |
| `GET` | `/v1/appointments/` | Get Appointments | OAuth2PasswordBearer | None | `200`: `List[AppointmentResponse]` |
| `POST` | `/v1/appointments/` | Create Appointment | OAuth2PasswordBearer | Body: `AppointmentCreate` | `200`: `AppointmentResponse`<br>`422`: `HTTPValidationError` |
| `POST` | `/v1/appointments/agent-chat` | Agent Chat Endpoint | OAuth2PasswordBearer | Body: `CASAChatRequest` | `200`: `json`<br>`422`: `HTTPValidationError` |
| `POST` | `/v1/appointments/agent-stream` | Agent Stream Endpoint | OAuth2PasswordBearer | Body: `CASAChatRequest` | `200`: `json`<br>`422`: `HTTPValidationError` |
| `GET` | `/v1/appointments/doctors` | Get Doctors | OAuth2PasswordBearer | None | `200`: `List[DoctorResponse]` |
| `GET` | `/v1/appointments/recommend-specialists/{patient_id}` | Recommend Specialists Based On Risks | OAuth2PasswordBearer | `patient_id` (path:integer:req) | `200`: `object`<br>`422`: `HTTPValidationError` |
| `POST` | `/v1/appointments/special-care` | Book Special Care Appointment | OAuth2PasswordBearer | Body: `SpecialCareBookingRequest` | `200`: `object`<br>`422`: `HTTPValidationError` |
| `DELETE` | `/v1/appointments/{appointment_id}` | Delete Appointment | OAuth2PasswordBearer | `appointment_id` (path:integer:req) | `200`: `json`<br>`422`: `HTTPValidationError` |
| `PUT` | `/v1/appointments/{appointment_id}/cancel` | Cancel Appointment | OAuth2PasswordBearer | `appointment_id` (path:integer:req) | `200`: `json`<br>`422`: `HTTPValidationError` |
| `PUT` | `/v1/appointments/{appointment_id}/reschedule` | Reschedule Appointment | OAuth2PasswordBearer | `appointment_id` (path:integer:req), `date` (query:string:req), `time` (query:string:req) | `200`: `json`<br>`422`: `HTTPValidationError` |

### 2.10 Top-Level & System (10 Endpoints)

| Method | Full Route Path | Summary / Description | Auth & Security | Request Body / Params | Response Codes & Schema |
| --- | --- | --- | --- | --- | --- |
| `GET` | `/` | Root | Public / None | None | `200`: `json` |
| `POST` | `/generate_report` | Generate Report | OAuth2PasswordBearer | None | `200`: `json` |
| `GET` | `/healthz` | Health | Public / None | None | `200`: `json` |
| `GET` | `/healthz/circuit_breaker` | Circuit Breaker | Public / None | None | `200`: `json` |
| `GET` | `/healthz/env` | Healthz Env | Public / None | None | `200`: `json` |
| `GET` | `/healthz/time_predict` | Time Predict | Public / None | None | `200`: `json` |
| `GET` | `/metrics` | Get Prometheus Metrics | Public / None | None | `200`: `json` |
| `POST` | `/v1/licensing/activate` | Activate License Key | Public / None | Body: `LicenseActivationPayload` | `200`: `json`<br>`422`: `HTTPValidationError` |
| `GET` | `/v1/licensing/status` | Get Licensing Status | Public / None | None | `200`: `json` |
| `GET` | `/{catchall}` | Serve Frontend | Public / None | `catchall` (path:string:req) | `200`: `json`<br>`422`: `HTTPValidationError` |

### 2.11 Diagnostics (9 Endpoints)

| Method | Full Route Path | Summary / Description | Auth & Security | Request Body / Params | Response Codes & Schema |
| --- | --- | --- | --- | --- | --- |
| `GET` | `/v1/diagnostics/admin/metrics` | Get Diagnostics Metrics | OAuth2PasswordBearer | None | `200`: `object` |
| `GET` | `/v1/diagnostics/doctor/patients/{patient_id}/results` | Get Doctor Patient Results | OAuth2PasswordBearer | `patient_id` (path:integer:req) | `200`: `object`<br>`422`: `HTTPValidationError` |
| `POST` | `/v1/diagnostics/ecg/analyze` | Analyze Ecg Telemetry | OAuth2PasswordBearer | Body: `object` | `200`: `object`<br>`422`: `HTTPValidationError` |
| `POST` | `/v1/diagnostics/lab-kits` | Order Lab Kit | OAuth2PasswordBearer | Body: `LabKitOrderRequest` | `200`: `object`<br>`422`: `HTTPValidationError` |
| `GET` | `/v1/diagnostics/lab-kits/{patient_id}` | Get Lab Kits | OAuth2PasswordBearer | `patient_id` (path:integer:req) | `200`: `object`<br>`422`: `HTTPValidationError` |
| `GET` | `/v1/diagnostics/patient/results` | Get Patient Results | OAuth2PasswordBearer | None | `200`: `List[DiagnosticResultResponse]` |
| `POST` | `/v1/diagnostics/results` | Post Diagnostic Result | OAuth2PasswordBearer | Body: `DiagnosticResultCreate` | `200`: `DiagnosticResultResponse`<br>`422`: `HTTPValidationError` |
| `PUT` | `/v1/diagnostics/results/{result_id}/review` | Review Diagnostic Result | OAuth2PasswordBearer | `result_id` (path:integer:req)<br>Body: `DiagnosticReviewUpdate` | `200`: `DiagnosticResultResponse`<br>`422`: `HTTPValidationError` |
| `POST` | `/v1/diagnostics/upload` | Upload Diagnostic File | OAuth2PasswordBearer | Body: `DiagnosticUploadCreate` | `200`: `object`<br>`422`: `HTTPValidationError` |

### 2.12 Chat (8 Endpoints)

| Method | Full Route Path | Summary / Description | Auth & Security | Request Body / Params | Response Codes & Schema |
| --- | --- | --- | --- | --- | --- |
| `POST` | `/v1/chat` | Chat Endpoint | OAuth2PasswordBearer | Body: `ChatRequest` | `200`: `json`<br>`422`: `HTTPValidationError` |
| `POST` | `/v1/chat/aura` | Aura Fallback Chat | OAuth2PasswordBearer | Body: `ChatRequest` | `200`: `json`<br>`422`: `HTTPValidationError` |
| `DELETE` | `/v1/chat/history` | Delete Chat History | OAuth2PasswordBearer | None | `200`: `json` |
| `GET` | `/v1/chat/history` | Get Chat History | OAuth2PasswordBearer | None | `200`: `json` |
| `GET` | `/v1/download/health-report` | Download Health Report | OAuth2PasswordBearer | None | `200`: `json` |
| `GET` | `/v1/records` | Get Health Records | OAuth2PasswordBearer | `record_type` (query:any:opt) | `200`: `List[HealthRecordResponse]`<br>`422`: `HTTPValidationError` |
| `POST` | `/v1/records` | Save Health Record | OAuth2PasswordBearer | Body: `RecordCreate` | `200`: `json`<br>`422`: `HTTPValidationError` |
| `DELETE` | `/v1/records/{record_id}` | Delete Health Record | OAuth2PasswordBearer | `record_id` (path:integer:req) | `200`: `json`<br>`422`: `HTTPValidationError` |

### 2.13 Nursing (7 Endpoints)

| Method | Full Route Path | Summary / Description | Auth & Security | Request Body / Params | Response Codes & Schema |
| --- | --- | --- | --- | --- | --- |
| `GET` | `/v1/nursing/admin/metrics` | Get Nursing Metrics | OAuth2PasswordBearer | None | `200`: `object` |
| `GET` | `/v1/nursing/doctor/patients/{patient_id}/tasks` | Get Doctor Patient Nursing Tasks | OAuth2PasswordBearer | `patient_id` (path:integer:req) | `200`: `object`<br>`422`: `HTTPValidationError` |
| `GET` | `/v1/nursing/nurse/tasks` | Get Nurse Tasks | OAuth2PasswordBearer | None | `200`: `List[NursingTaskResponse]` |
| `GET` | `/v1/nursing/patient/tasks` | Get Patient Nursing Tasks | OAuth2PasswordBearer | None | `200`: `List[NursingTaskResponse]` |
| `POST` | `/v1/nursing/patients/{patient_id}/handoff` | Generate Nursing Handoff Card | OAuth2PasswordBearer | `patient_id` (path:integer:req) | `200`: `json`<br>`422`: `HTTPValidationError` |
| `POST` | `/v1/nursing/tasks` | Create Nursing Task | OAuth2PasswordBearer | Body: `NursingTaskCreate` | `200`: `NursingTaskResponse`<br>`422`: `HTTPValidationError` |
| `PUT` | `/v1/nursing/tasks/{task_id}/complete` | Complete Nursing Task | OAuth2PasswordBearer | `task_id` (path:integer:req)<br>Body: `NursingTaskComplete` | `200`: `NursingTaskResponse`<br>`422`: `HTTPValidationError` |

### 2.14 Monitoring (6 Endpoints)

| Method | Full Route Path | Summary / Description | Auth & Security | Request Body / Params | Response Codes & Schema |
| --- | --- | --- | --- | --- | --- |
| `GET` | `/v1/monitoring/admin/patterns` | Get Admin Patterns | OAuth2PasswordBearer | None | `200`: `object` |
| `GET` | `/v1/monitoring/doctor/patients/{patient_id}/signals` | Get Patient Signals For Doctor | OAuth2PasswordBearer | `patient_id` (path:integer:req) | `200`: `object`<br>`422`: `HTTPValidationError` |
| `GET` | `/v1/monitoring/doctor/patterns` | Get Doctor Patterns | OAuth2PasswordBearer | None | `200`: `object` |
| `GET` | `/v1/monitoring/patient/vitals` | Get Patient Vitals | OAuth2PasswordBearer | None | `200`: `List[VitalObservationResponse]` |
| `PUT` | `/v1/monitoring/signals/{signal_id}/resolve` | Resolve Monitoring Signal | OAuth2PasswordBearer | `signal_id` (path:integer:req) | `200`: `MonitoringSignalResponse`<br>`422`: `HTTPValidationError` |
| `POST` | `/v1/monitoring/vitals` | Submit Vitals | OAuth2PasswordBearer | Body: `VitalObservationCreate` | `200`: `VitalSubmissionResponse`<br>`422`: `HTTPValidationError` |

### 2.15 Discharge (6 Endpoints)

| Method | Full Route Path | Summary / Description | Auth & Security | Request Body / Params | Response Codes & Schema |
| --- | --- | --- | --- | --- | --- |
| `GET` | `/v1/discharge/admin/metrics` | Get Discharge Metrics | OAuth2PasswordBearer | None | `200`: `object` |
| `GET` | `/v1/discharge/doctor/patients/{patient_id}/summaries` | Get Doctor Patient Discharge Summaries | OAuth2PasswordBearer | `patient_id` (path:integer:req) | `200`: `object`<br>`422`: `HTTPValidationError` |
| `GET` | `/v1/discharge/patient/summaries` | Get Patient Discharge Summaries | OAuth2PasswordBearer | None | `200`: `List[DischargeSummaryResponse]` |
| `POST` | `/v1/discharge/summaries` | Create Discharge Summary | OAuth2PasswordBearer | Body: `DischargeSummaryCreate` | `200`: `DischargeSummaryResponse`<br>`422`: `HTTPValidationError` |
| `POST` | `/v1/discharge/summaries/generate/{patient_id}` | Auto Generate Discharge Summary | OAuth2PasswordBearer | `patient_id` (path:integer:req) | `200`: `json`<br>`422`: `HTTPValidationError` |
| `PUT` | `/v1/discharge/summaries/{summary_id}/finalize` | Finalize Discharge Summary | OAuth2PasswordBearer | `summary_id` (path:integer:req) | `200`: `DischargeSummaryResponse`<br>`422`: `HTTPValidationError` |

### 2.16 Care Events (6 Endpoints)

| Method | Full Route Path | Summary / Description | Auth & Security | Request Body / Params | Response Codes & Schema |
| --- | --- | --- | --- | --- | --- |
| `GET` | `/v1/events/admin/metrics` | Get Admin Event Metrics | OAuth2PasswordBearer | None | `200`: `object` |
| `GET` | `/v1/events/admin/patients/{patient_id}/feed` | Get Admin Patient Event Feed | OAuth2PasswordBearer | `patient_id` (path:integer:req), `after_id` (query:any:opt), `limit` (query:integer:opt) | `200`: `object`<br>`422`: `HTTPValidationError` |
| `GET` | `/v1/events/admin/recent` | Get Admin Recent Events | OAuth2PasswordBearer | `after_id` (query:any:opt), `limit` (query:integer:opt) | `200`: `object`<br>`422`: `HTTPValidationError` |
| `POST` | `/v1/events/dispatch` | Dispatch Care Event | OAuth2PasswordBearer | Body: `CareEventCreate` | `200`: `object`<br>`422`: `HTTPValidationError` |
| `GET` | `/v1/events/doctor/patients/{patient_id}/feed` | Get Doctor Patient Event Feed | OAuth2PasswordBearer | `patient_id` (path:integer:req), `after_id` (query:any:opt), `limit` (query:integer:opt) | `200`: `object`<br>`422`: `HTTPValidationError` |
| `GET` | `/v1/events/patient/feed` | Get Patient Event Feed | OAuth2PasswordBearer | `after_id` (query:any:opt), `limit` (query:integer:opt) | `200`: `object`<br>`422`: `HTTPValidationError` |

### 2.17 Telemetry (6 Endpoints)

| Method | Full Route Path | Summary / Description | Auth & Security | Request Body / Params | Response Codes & Schema |
| --- | --- | --- | --- | --- | --- |
| `GET` | `/telemetry/health` | Get Telemetry Health | Public / None | None | `200`: `object` |
| `POST` | `/telemetry/hl7_ingest` | Ingest Hl7 | OAuth2PasswordBearer | Body: `string` | `200`: `json`<br>`422`: `HTTPValidationError` |
| `GET` | `/telemetry/snapshot` | Get Telemetry Snapshot | OAuth2PasswordBearer | None | `200`: `object` |
| `GET` | `/v1/telemetry/health` | Get Telemetry Health | Public / None | None | `200`: `object` |
| `POST` | `/v1/telemetry/hl7_ingest` | Ingest Hl7 | OAuth2PasswordBearer | Body: `string` | `200`: `json`<br>`422`: `HTTPValidationError` |
| `GET` | `/v1/telemetry/snapshot` | Get Telemetry Snapshot | OAuth2PasswordBearer | None | `200`: `object` |

### 2.18 FHIR R4 (6 Endpoints)

| Method | Full Route Path | Summary / Description | Auth & Security | Request Body / Params | Response Codes & Schema |
| --- | --- | --- | --- | --- | --- |
| `GET` | `/v1/fhir/AuditEvent` | Get Fhir Audit Events | HTTPBearer | None | `200`: `object` |
| `GET` | `/v1/fhir/Claim` | Search Claims | HTTPBearer | `patient` (query:any:opt) | `200`: `object`<br>`422`: `HTTPValidationError` |
| `GET` | `/v1/fhir/ImagingStudy` | Search Imaging Studies | HTTPBearer | `patient` (query:any:opt) | `200`: `object`<br>`422`: `HTTPValidationError` |
| `GET` | `/v1/fhir/Observation` | Get Fhir Observations | HTTPBearer | `patient` (query:integer:req) | `200`: `array`<br>`422`: `HTTPValidationError` |
| `POST` | `/v1/fhir/Patient/import/{external_fhir_id}` | Import Fhir Patient | Public / None | `external_fhir_id` (path:string:req) | `201`: `object`<br>`422`: `HTTPValidationError` |
| `GET` | `/v1/fhir/Patient/{patient_id}` | Get Fhir Patient | HTTPBearer | `patient_id` (path:integer:req) | `200`: `object`<br>`422`: `HTTPValidationError` |

### 2.19 Lakehouse Data Engineering (6 Endpoints)

| Method | Full Route Path | Summary / Description | Auth & Security | Request Body / Params | Response Codes & Schema |
| --- | --- | --- | --- | --- | --- |
| `GET` | `/v1/lakehouse/delta/cdf` | Read Delta Lake Change Data Feed (CDF) Stream | Public / None | `table_name` (query:string:opt), `start_version` (query:integer:opt), `end_version` (query:integer:opt) | `200`: `array`<br>`422`: `HTTPValidationError` |
| `GET` | `/v1/lakehouse/delta/history` | Inspect Delta Lake Commit Log & History | Public / None | `table_name` (query:string:opt) | `200`: `array`<br>`422`: `HTTPValidationError` |
| `POST` | `/v1/lakehouse/delta/restore` | Execute ACID Table Rollback / Restore | Public / None | Body: `RestoreTableRequest` | `200`: `object`<br>`422`: `HTTPValidationError` |
| `POST` | `/v1/lakehouse/delta/time-travel` | Query Delta Lake Snapshot at Historical Version | Public / None | Body: `TimeTravelRequest` | `200`: `object`<br>`422`: `HTTPValidationError` |
| `POST` | `/v1/lakehouse/omop/transform` | Transform FHIR / EHR Payload to OMOP CDM v5.4 | Public / None | Body: `RawPatientPayload` | `200`: `object`<br>`422`: `HTTPValidationError` |
| `POST` | `/v1/lakehouse/quality/audit` | Execute Great Expectations Quality Gate & Quarantine Routing | Public / None | Body: `QualityAuditRequest` | `200`: `object`<br>`422`: `HTTPValidationError` |

### 2.20 SMART on FHIR (5 Endpoints)

| Method | Full Route Path | Summary / Description | Auth & Security | Request Body / Params | Response Codes & Schema |
| --- | --- | --- | --- | --- | --- |
| `GET` | `/v1/smart/apps` | List Smart Apps | OAuth2PasswordBearer | None | `200`: `List[SmartAppResponse]` |
| `POST` | `/v1/smart/apps` | Register Smart App | OAuth2PasswordBearer | Body: `SmartAppCreate` | `201`: `SmartAppResponse`<br>`422`: `HTTPValidationError` |
| `DELETE` | `/v1/smart/apps/{app_id}` | Delete Smart App | OAuth2PasswordBearer | `app_id` (path:integer:req) | `200`: `object`<br>`422`: `HTTPValidationError` |
| `POST` | `/v1/smart/launch` | Launch Smart App | OAuth2PasswordBearer | Body: `SmartLaunchRequest` | `200`: `SmartLaunchResponse`<br>`422`: `HTTPValidationError` |
| `POST` | `/v1/smart/token` | Exchange Token | Public / None | Body: `Body_exchange_token_v1_smart_token_post` | `200`: `json`<br>`422`: `HTTPValidationError` |

### 2.21 Recommendation Engine (5 Endpoints)

| Method | Full Route Path | Summary / Description | Auth & Security | Request Body / Params | Response Codes & Schema |
| --- | --- | --- | --- | --- | --- |
| `POST` | `/v1/recommendations/clinical-interventions` | Generate Personalized Clinical Interventions | Public / None | Body: `RecommendationRequest` | `200`: `RecommendationResponse`<br>`422`: `HTTPValidationError` |
| `POST` | `/v1/recommendations/clinical-trials` | Match Patient to Investigational Clinical Trials | Public / None | Body: `RecommendationRequest` | `200`: `RecommendationResponse`<br>`422`: `HTTPValidationError` |
| `POST` | `/v1/recommendations/feedback` | Record Clinician / Patient Feedback for Bandit Online Learning | Public / None | Body: `FeedbackEvent` | `200`: `object`<br>`422`: `HTTPValidationError` |
| `POST` | `/v1/recommendations/generate` | Generic Multi-Stage Recommendation Engine Entrypoint | Public / None | Body: `RecommendationRequest` | `200`: `RecommendationResponse`<br>`422`: `HTTPValidationError` |
| `POST` | `/v1/recommendations/lifestyle-pathways` | Generate Personalized Lifestyle Pathways | Public / None | Body: `RecommendationRequest` | `200`: `RecommendationResponse`<br>`422`: `HTTPValidationError` |

### 2.22 Four-Eye Clinical Governance & AI Safety (5 Endpoints)

| Method | Full Route Path | Summary / Description | Auth & Security | Request Body / Params | Response Codes & Schema |
| --- | --- | --- | --- | --- | --- |
| `POST` | `/v1/governance/ai-guardian/evaluate` | Evaluate Ai Safety Pipeline | OAuth2PasswordBearer | Body: `AIEvaluationPayload` | `200`: `GovernanceCheckResult`<br>`422`: `HTTPValidationError` |
| `GET` | `/v1/governance/four-eye/pending` | List Pending Four Eye Reviews | OAuth2PasswordBearer | None | `200`: `List[FourEyeCheckRequest]` |
| `POST` | `/v1/governance/four-eye/review` | Peer Review Action | OAuth2PasswordBearer | Body: `FourEyeReviewPayload` | `200`: `FourEyeCheckRequest`<br>`422`: `HTTPValidationError` |
| `POST` | `/v1/governance/four-eye/submit` | Submit For Four Eye Review | OAuth2PasswordBearer | Body: `FourEyeSubmitPayload` | `201`: `FourEyeCheckRequest`<br>`422`: `HTTPValidationError` |
| `GET` | `/v1/governance/four-eye/verify/{request_id}` | Verify Four Eye Signature | OAuth2PasswordBearer | `request_id` (path:string:req) | `200`: `object`<br>`422`: `HTTPValidationError` |

### 2.23 Ollama Models (4 Endpoints)

| Method | Full Route Path | Summary / Description | Auth & Security | Request Body / Params | Response Codes & Schema |
| --- | --- | --- | --- | --- | --- |
| `DELETE` | `/v1/ai/models` | Delete Model | OAuth2PasswordBearer | Body: `DeleteModelRequest` | `200`: `json`<br>`422`: `HTTPValidationError` |
| `GET` | `/v1/ai/models` | List Models | OAuth2PasswordBearer | None | `200`: `json` |
| `GET` | `/v1/ai/models/library` | Get Library | OAuth2PasswordBearer | None | `200`: `json` |
| `POST` | `/v1/ai/models/pull` | Pull Model | OAuth2PasswordBearer | Body: `PullModelRequest` | `200`: `json`<br>`422`: `HTTPValidationError` |

### 2.24 Longitudinal Predictions (4 Endpoints)

| Method | Full Route Path | Summary / Description | Auth & Security | Request Body / Params | Response Codes & Schema |
| --- | --- | --- | --- | --- | --- |
| `POST` | `/v1/predict/longitudinal/diabetes` | Predict Longitudinal Diabetes | OAuth2PasswordBearer | Body: `LongitudinalDiabetesRequest` | `200`: `LongitudinalPredictionResponse`<br>`422`: `HTTPValidationError` |
| `POST` | `/v1/predict/longitudinal/heart` | Predict Longitudinal Heart | OAuth2PasswordBearer | Body: `LongitudinalHeartRequest` | `200`: `LongitudinalPredictionResponse`<br>`422`: `HTTPValidationError` |
| `POST` | `/v1/predict/longitudinal/kidney` | Predict Longitudinal Kidney | OAuth2PasswordBearer | Body: `LongitudinalKidneyRequest` | `200`: `LongitudinalPredictionResponse`<br>`422`: `HTTPValidationError` |
| `POST` | `/v1/predict/longitudinal/liver` | Predict Longitudinal Liver | OAuth2PasswordBearer | Body: `LongitudinalLiverRequest` | `200`: `LongitudinalPredictionResponse`<br>`422`: `HTTPValidationError` |

### 2.25 Federated Learning (4 Endpoints)

| Method | Full Route Path | Summary / Description | Auth & Security | Request Body / Params | Response Codes & Schema |
| --- | --- | --- | --- | --- | --- |
| `GET` | `/v1/federated/audits` | Get Sync Audits | OAuth2PasswordBearer | None | `200`: `List[FederatedSyncAuditResponse]` |
| `POST` | `/v1/federated/feedback` | Submit Model Feedback | OAuth2PasswordBearer | Body: `ModelFeedbackCreate` | `201`: `ModelFeedbackResponse`<br>`422`: `HTTPValidationError` |
| `GET` | `/v1/federated/stats` | Get Federated Stats | OAuth2PasswordBearer | None | `200`: `object` |
| `POST` | `/v1/federated/sync` | Trigger Federated Sync | OAuth2PasswordBearer | Body: `FederatedSyncRequest` | `200`: `FederatedSyncResponse`<br>`422`: `HTTPValidationError` |

### 2.26 Clinical Intelligence (4 Endpoints)

| Method | Full Route Path | Summary / Description | Auth & Security | Request Body / Params | Response Codes & Schema |
| --- | --- | --- | --- | --- | --- |
| `GET` | `/v1/intelligence/alerts` | List Clinical Alerts | OAuth2PasswordBearer | `severity` (query:any:opt), `patient_id` (query:any:opt) | `200`: `List[ClinicalAlertResponse]`<br>`422`: `HTTPValidationError` |
| `POST` | `/v1/intelligence/alerts/{alert_id}/acknowledge` | Acknowledge Alert | OAuth2PasswordBearer | `alert_id` (path:integer:req) | `200`: `object`<br>`422`: `HTTPValidationError` |
| `GET` | `/v1/intelligence/explainability/{prediction_id}` | Get Prediction Explainability | OAuth2PasswordBearer | `prediction_id` (path:integer:req) | `200`: `ExplainabilityResponse`<br>`422`: `HTTPValidationError` |
| `GET` | `/v1/intelligence/insights/{patient_id}` | Generate Patient Insights | OAuth2PasswordBearer | `patient_id` (path:integer:req) | `200`: `PatientInsightResponse`<br>`422`: `HTTPValidationError` |

### 2.27 ABDM Sandbox (4 Endpoints)

| Method | Full Route Path | Summary / Description | Auth & Security | Request Body / Params | Response Codes & Schema |
| --- | --- | --- | --- | --- | --- |
| `POST` | `/v1/abdm/abha/generate` | Generate Abha Health Id | Public / None | Body: `ABHACreateRequest` | `200`: `ABHAResponse`<br>`422`: `HTTPValidationError` |
| `GET` | `/v1/abdm/abha/{abha_number}` | Get Abha Details | Public / None | `abha_number` (path:string:req) | `200`: `ABHAResponse`<br>`422`: `HTTPValidationError` |
| `POST` | `/v1/abdm/consent/request` | Request Health Consent | Public / None | Body: `ConsentArtifactCreate` | `200`: `ConsentArtifactResponse`<br>`422`: `HTTPValidationError` |
| `GET` | `/v1/abdm/consent/{consent_id}` | Get Consent Status | Public / None | `consent_id` (path:string:req) | `200`: `ConsentArtifactResponse`<br>`422`: `HTTPValidationError` |

### 2.28 Streaming Chat (3 Endpoints)

| Method | Full Route Path | Summary / Description | Auth & Security | Request Body / Params | Response Codes & Schema |
| --- | --- | --- | --- | --- | --- |
| `GET` | `/v1/chat/context` | Chat Context Endpoint | OAuth2PasswordBearer | `q` (query:string:opt) | `200`: `json`<br>`422`: `HTTPValidationError` |
| `POST` | `/v1/chat/stream` | Stream Chat | OAuth2PasswordBearer | `x-ai-provider` (header:any:opt), `x-ai-api-key` (header:any:opt)<br>Body: `StreamChatRequest` | `200`: `json`<br>`422`: `HTTPValidationError` |
| `GET` | `/v1/chat/suggestions` | Chat Suggestions | OAuth2PasswordBearer | None | `200`: `json` |

### 2.29 DICOMweb PACS (3 Endpoints)

| Method | Full Route Path | Summary / Description | Auth & Security | Request Body / Params | Response Codes & Schema |
| --- | --- | --- | --- | --- | --- |
| `POST` | `/v1/dicomweb/calibrate-hu` | Calibrate Hounsfield Units | Public / None | Body: `object` | `200`: `object`<br>`422`: `HTTPValidationError` |
| `GET` | `/v1/dicomweb/studies` | Qido Rs Search Studies | Public / None | `StudyInstanceUID` (query:any:opt) | `200`: `json`<br>`422`: `HTTPValidationError` |
| `GET` | `/v1/dicomweb/studies/{study_uid}/metadata` | Wado Rs Retrieve Metadata | Public / None | `study_uid` (path:string:req) | `200`: `json`<br>`422`: `HTTPValidationError` |

### 2.30 i18n Audio (3 Endpoints)

| Method | Full Route Path | Summary / Description | Auth & Security | Request Body / Params | Response Codes & Schema |
| --- | --- | --- | --- | --- | --- |
| `POST` | `/v1/audio/transcribe` | Transcribe Audio | Public / None | Body: `Body_transcribe_audio_v1_audio_transcribe_post` | `200`: `json`<br>`422`: `HTTPValidationError` |
| `POST` | `/v1/audio/translate` | Translate Text | Public / None | Body: `TranslationRequest` | `200`: `json`<br>`422`: `HTTPValidationError` |
| `POST` | `/v1/audio/tts` | Text To Speech | Public / None | Body: `TTSRequest` | `200`: `json`<br>`422`: `HTTPValidationError` |

### 2.31 Peak Healthcare Intelligence (3 Endpoints)

| Method | Full Route Path | Summary / Description | Auth & Security | Request Body / Params | Response Codes & Schema |
| --- | --- | --- | --- | --- | --- |
| `POST` | `/v1/clinical-council/deliberate` | Deliberate Complex Cases with Multi-Specialist AI Council | Public / None | Body: `ClinicalCouncilDeliberationRequest` | `200`: `ClinicalCouncilConsensusResponse`<br>`422`: `HTTPValidationError` |
| `POST` | `/v1/digital-twin/simulate` | Simulate 10-Year Multi-Organ Clinical Trajectory | Public / None | Body: `DigitalTwinSimulationRequest` | `200`: `DigitalTwinSimulationResponse`<br>`422`: `HTTPValidationError` |
| `POST` | `/v1/pharmacogenomics/evaluate` | Evaluate CPIC Precision Pharmacogenomics | Public / None | Body: `PharmacogenomicEvaluationRequest` | `200`: `PharmacogenomicEvaluationResponse`<br>`422`: `HTTPValidationError` |

### 2.32 Reports (2 Endpoints)

| Method | Full Route Path | Summary / Description | Auth & Security | Request Body / Params | Response Codes & Schema |
| --- | --- | --- | --- | --- | --- |
| `POST` | `/v1/analyze/report` | Analyze Report | OAuth2PasswordBearer | Body: `Body_analyze_report_v1_analyze_report_post` | `200`: `object`<br>`422`: `HTTPValidationError` |
| `GET` | `/v1/reports/download/health-report` | Download Health Report | OAuth2PasswordBearer | None | `200`: `json` |

### 2.33 Payments (2 Endpoints)

| Method | Full Route Path | Summary / Description | Auth & Security | Request Body / Params | Response Codes & Schema |
| --- | --- | --- | --- | --- | --- |
| `POST` | `/v1/payments/create-order` | Create Order | OAuth2PasswordBearer | Body: `OrderRequest` | `200`: `json`<br>`422`: `HTTPValidationError` |
| `POST` | `/v1/payments/verify` | Verify Payment | OAuth2PasswordBearer | Body: `VerifyRequest` | `200`: `json`<br>`422`: `HTTPValidationError` |

### 2.34 Consent (2 Endpoints)

| Method | Full Route Path | Summary / Description | Auth & Security | Request Body / Params | Response Codes & Schema |
| --- | --- | --- | --- | --- | --- |
| `POST` | `/v1/consent/accept` | Accept Eula | OAuth2PasswordBearer | Body: `ConsentAcceptRequest` | `200`: `json`<br>`422`: `HTTPValidationError` |
| `GET` | `/v1/consent/status` | Consent Status | OAuth2PasswordBearer | None | `200`: `json` |

### 2.35 FHIR Compression (2 Endpoints)

| Method | Full Route Path | Summary / Description | Auth & Security | Request Body / Params | Response Codes & Schema |
| --- | --- | --- | --- | --- | --- |
| `POST` | `/v1/fhir/compact` | Compact Fhir | Public / None | Body: `CompactRequest` | `200`: `json`<br>`422`: `HTTPValidationError` |
| `POST` | `/v1/fhir/decompress` | Decompress Fhir | Public / None | Body: `DecompressRequest` | `200`: `json`<br>`422`: `HTTPValidationError` |

### 2.36 Multi-Cloud Pipeline Mesh (2 Endpoints)

| Method | Full Route Path | Summary / Description | Auth & Security | Request Body / Params | Response Codes & Schema |
| --- | --- | --- | --- | --- | --- |
| `POST` | `/v1/mesh/run` | Trigger Mesh Pipeline Run | Public / None | Body: `MeshPipelineRunRequest` | `200`: `MeshPipelineRunResult`<br>`422`: `HTTPValidationError` |
| `GET` | `/v1/mesh/status` | Get Mesh Status | Public / None | None | `200`: `json` |

### 2.37 Explanation (1 Endpoints)

| Method | Full Route Path | Summary / Description | Auth & Security | Request Body / Params | Response Codes & Schema |
| --- | --- | --- | --- | --- | --- |
| `POST` | `/v1/explain/` | Explain Prediction | OAuth2PasswordBearer | Body: `backend__explanation__ExplanationRequest` | `200`: `ExplanationResponse`<br>`422`: `HTTPValidationError` |

### 2.38 Sales Readiness (1 Endpoints)

| Method | Full Route Path | Summary / Description | Auth & Security | Request Body / Params | Response Codes & Schema |
| --- | --- | --- | --- | --- | --- |
| `GET` | `/v1/admin/sales-readiness` | Get Sales Readiness | OAuth2PasswordBearer | None | `200`: `object` |

### 2.39 Demo Readiness (1 Endpoints)

| Method | Full Route Path | Summary / Description | Auth & Security | Request Body / Params | Response Codes & Schema |
| --- | --- | --- | --- | --- | --- |
| `GET` | `/v1/demo-readiness/` | Get Demo Readiness | Public / None | None | `200`: `object` |

---
## 3. Real-Time Streaming & WebSocket Specifications

### 3.1 Telemetry Streaming WebSockets
- **Routes**: `/v1/telemetry/stream` and `/telemetry/stream`
- **Protocol**: WebSocket (`ws://` / `wss://`)
- **Authentication**: Query parameter `?token=<JWT_ACCESS_TOKEN>`
- **Authorization**: Admin only (`auth.is_admin(current_user) == True`). Rejects unauthorized clients with WebSocket Close code `1008` (Policy Violation).
- **Push Frequency**: Emits real-time hospital telemetry snapshot every 2.0 seconds.
- **Message Payload Schema (JSON)**:
```json
{
  "timestamp": "2026-08-21T05:15:00.000Z",
  "facility_id": 1,
  "source": "database",
  "active_census": 42,
  "total_capacity": 100,
  "open_monitoring_signals": 3,
  "system_latency_ms": 12,
  "spark_batch_id": 1024,
  "spark_records_processed": 16,
  "spark_ml_latency_ms": 3.2,
  "is_real_stream": false,
  "ai_nodes_active": 12,
  "cpu_percent": 14.5,
  "ram_percent": 45.2,
  "hl7_logs": [
    {
      "id": "1724217300.12",
      "time": "10:45:00",
      "msg": "[REDACTED] ADT^A01..."
    }
  ],
  "ed_boarding": 14,
  "ed_avg_wait_min": 115,
  "pending_discharges": 6,
  "confirmed_discharges": 3,
  "surge_prediction_pct": 15,
  "department_loads": [
    {
      "dept": "ICU-A",
      "load": 90,
      "status": "Critical"
    }
  ],
  "bed_units": [
    {
      "unit": "ICU-A",
      "total": 20,
      "occupied": 18,
      "cleaning": 1,
      "available": 1
    }
  ]
}
```

### 3.2 Patient Vitals Live Stream WebSocket
- **Routes**: `/v1/telemetry/vitals/{patient_id}` and `/telemetry/vitals/{patient_id}`
- **Protocol**: WebSocket (`ws://` / `wss://`)
- **Authentication**: Query parameter `?token=<JWT_ACCESS_TOKEN>`
- **Push Behavior**: Checks for newly recorded `VitalObservation` records every 2.0 seconds and pushes update if `observed_at` timestamp changed.
- **Message Payload Schema (JSON)**:
```json
{
  "heart_rate": 78.0,
  "systolic_bp": 120.0,
  "diastolic_bp": 80.0,
  "spo2": 98.5,
  "temperature_c": 36.8,
  "blood_glucose": 95.0,
  "observed_at": "2026-08-21T05:15:00.000Z"
}
```

### 3.3 Server-Sent Events (SSE) AI Streaming Chat
- **Route**: `POST /v1/chat/stream`
- **Headers**: `Content-Type: application/json`, `Authorization: Bearer <token>`, optional `x-ai-provider: <str>`, `x-ai-api-key: <str>`
- **Response Media Type**: `text/event-stream`
- **SSE Event Sequence**:
  1. Metadata chunk: `data: {"sources": [...], "model": "llama3", "status": "starting"}`
  2. Optional Tool Call: `data: {"status": "tool_call", "tool": "Clinical Analyzer", "details": "..."}`
  3. Token stream chunks: `data: {"reply": "token_chunk"}`
  4. Heartbeat keepalives (every 15s idle): `:heartbeat (keepalive)`
  5. Completion event: `data: {"reply": "\n\n*Medical Disclaimer*"}` followed by `data: {"status": "complete"}`

---
## 4. Authentication, Authorization & Security Architecture

### 4.1 Token Issuance & Verification
- **Token Endpoint**: `POST /v1/token`
- **Payload Format**: Form URL Encoded (`OAuth2PasswordRequestForm`: `username`, `password`, optional `totp_code`)
- **Brute-Force Guard**: 5 consecutive failed attempts trigger a 15-minute account lockout.
- **Token Format**: JWT with `HS256` signature.
- **Claims**: `{"sub": "<username>", "exp": <timestamp>}`
- **Expiration**: Default 525,600 minutes (configurable via `ACCESS_TOKEN_EXPIRE_MINUTES`).
- **Header Scheme**: `Authorization: Bearer <access_token>`

### 4.2 Multi-Factor Authentication (2FA / TOTP)
- `POST /v1/2fa/setup`: Generates Base32 TOTP secret & PNG QR Code data URI (`schemas.TOTPSetupResponse`).
- `POST /v1/2fa/enable`: Accepts 6-digit TOTP code (`schemas.TOTPVerifyRequest`), validates against secret, enables 2FA flag on user.

### 4.3 Multi-Tenant Isolation & Role Hierarchy
- **Roles**: `admin`, `doctor`, `nurse`, `patient`, `auditor`, `billing_specialist`
- **Facility Scoping**: Users, Beds, Departments, Encounters, Admissions, Orders, Diagnostics, Prescriptions are tagged with `facility_id`.
- **Licensing Gate**: `licensing.enforce_license_tier(...)` checks `LICENSE_KEY` for tiers (`community`, `clinical`, `enterprise`).

---
## 5. Frontend API Contract Matrix

The React SPA (`frontend/src/`) communicates via `frontend/src/lib/apiCore.ts` (base URL `http://127.0.0.1:8000/v1`).

| Frontend Module | UI Consumer Pages | Primary Backend Endpoints Called |
| --- | --- | --- |
| `apiAuth.ts` | Login, Signup, Profile, Settings | `/v1/token`, `/v1/signup`, `/v1/profile`, `/v1/me`, `/v1/2fa/*`, `/v1/forgot-password`, `/v1/reset-password` |
| `apiPredictions.ts` | Disease Predictor Pages | `/v1/predict/heart`, `/v1/predict/diabetes`, `/v1/predict/kidney`, `/v1/predict/liver`, `/v1/predict/lungs`, `/v1/predict/stroke`, `/v1/predict/multi-organ`, `/v1/predict/advisory-board/*`, `/v1/predict/consensus/*`, `/v1/predict/scribe/*` |
| `apiHospital.ts` | Hospital Operations, Admissions, Beds | `/v1/hospital/departments`, `/v1/hospital/beds`, `/v1/hospital/encounters`, `/v1/hospital/admissions`, `/v1/hospital/orders`, `/v1/hospital/doctor/patients`, `/v1/hospital/triage-queue`, `/v1/hospital/admin/operations` |
| `apiAdmin.ts` | Admin Dashboard, Governance, Audit | `/v1/admin/stats`, `/v1/admin/users`, `/v1/admin/patients`, `/v1/admin/audit-logs`, `/v1/admin/model-cards`, `/v1/admin/maintenance`, `/v1/admin/agents/*` |
| `apiBilling.ts` | Billing, Claims, Licensing | `/v1/billing/admin/metrics`, `/v1/billing/claims/submit`, `/v1/billing/estimate`, `/v1/licensing/status`, `/v1/licensing/activate` |
| `apiChat.ts` | AI Copilot Chat | `/v1/chat`, `/v1/chat/stream`, `/v1/chat/context`, `/v1/chat/suggestions`, `/v1/chat/history` |
| `apiIntelligence.ts` | Clinical Studio, Alerts | `/v1/intelligence/alerts`, `/v1/intelligence/insights/*`, `/v1/intelligence/explainability/*` |
| `apiLakehouse.ts` | Data Lakehouse Studio | `/api/v1/data-platform/sql/execute`, `/api/v1/data-platform/bi/ask`, `/v1/lakehouse/*` |
| `useTelemetry.ts` | Dashboard Telemetry Signals | WebSocket `/v1/telemetry/stream`, `/v1/telemetry/snapshot`, `/v1/telemetry/health` |

---
## 6. Target Rust + Bun Migration Architecture

### 6.1 Bun ElysiaJS Edge Entrypoint (PID 1)
- Handles routing, CORS, Gzip compression, JWT validation middleware, request caching (10s TTL on GET), and static asset serving for `frontend/dist`.
- Proxies API requests `/v1/*` to Rust Axum backend on `127.0.0.1:8001`.
- Upgrades and transparently proxies WebSocket connections `/v1/telemetry/stream` and `/v1/telemetry/vitals/:patient_id` directly to Axum.

### 6.2 Rust Axum Core Backend
- Implements all 305 HTTP operations with typed Axum extractors (`Json<T>`, `Query<T>`, `Path<T>`, `State<AppState>`).
- Uses `sqlx` with connection pooling supporting SQLite (`DATABASE_URL=sqlite:///./healthcare.db`) and PostgreSQL.
- ML disease prediction endpoints (`/v1/predict/*`) run native ONNX Runtime Rust (`ort` crate) loading `.onnx` models.

---
## 7. Component Schemas & Data Transfer Objects (DTOs)

Total Schemas Defined in Components: 165

### 7.ABDMConsentCallbackCreate (`ABDMConsentCallbackCreate`)
| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `patient_id` | `any` | No | Patient Id |
| `local_consent_id` | `any` | No | Local Consent Id |
| `abdm_request_id` | `string` | Yes | Abdm Request Id |
| `abdm_consent_id` | `any` | No | Abdm Consent Id |
| `status` | `string` | Yes | Status |
| `hi_types` | `any` | No | Hi Types |
| `event_type` | `any` | No | Event Type |
| `notification_at` | `any` | No | Notification At |
| `error_code` | `any` | No | Error Code |

### 7.ABDMConsentRequestCreate (`ABDMConsentRequestCreate`)
| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `patient_id` | `integer` | Yes | Patient Id |
| `patient_abha_address` | `string` | Yes | Patient Abha Address |
| `purpose_code` | `string` | No | Purpose Code |
| `hi_types` | `any` | No | Hi Types |
| `date_from` | `string` | Yes | Date From |
| `date_to` | `string` | Yes | Date To |
| `data_erase_at` | `string` | Yes | Data Erase At |
| `hip_id` | `any` | No | Hip Id |
| `care_context_reference` | `any` | No | Care Context Reference |
| `submit` | `boolean` | No | Submit |

### 7.ABHACreateRequest (`ABHACreateRequest`)
| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `name` | `string` | Yes | Name |
| `gender` | `string` | No | Gender |
| `year_of_birth` | `integer` | No | Year Of Birth |
| `mobile` | `string` | Yes | Mobile |
| `aadhaar_last4` | `any` | No | Aadhaar Last4 |

### 7.ABHAResponse (`ABHAResponse`)
| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `abha_number` | `string` | Yes | Abha Number |
| `abha_address` | `string` | Yes | Abha Address |
| `name` | `string` | Yes | Name |
| `status` | `string` | Yes | Status |
| `qr_code_token` | `string` | Yes | Qr Code Token |
| `created_at` | `string` | Yes | Created At |

### 7.AIEvaluationPayload (`AIEvaluationPayload`)
| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `prompt_or_advice` | `string` | Yes | Prompt Or Advice |
| `patient_id` | `any` | No | Patient Id |
| `predicted_probability` | `any` | No | Predicted Probability |
| `confidence_interval_width` | `any` | No | Confidence Interval Width |
| `allergies` | `any` | No | Allergies |
| `medication_name` | `any` | No | Medication Name |

### 7.AdmissionCreate (`AdmissionCreate`)
| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `encounter_id` | `integer` | Yes | Encounter Id |
| `patient_id` | `integer` | Yes | Patient Id |
| `doctor_id` | `any` | No | Doctor Id |
| `department_id` | `any` | No | Department Id |
| `bed_id` | `any` | No | Bed Id |
| `admitted_at` | `any` | No | Admitted At |
| `reason` | `any` | No | Reason |

### 7.AdmissionResponse (`AdmissionResponse`)
| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `id` | `integer` | Yes | Id |
| `facility_id` | `any` | No | Facility Id |
| `encounter_id` | `integer` | Yes | Encounter Id |
| `patient_id` | `integer` | Yes | Patient Id |
| `doctor_id` | `any` | No | Doctor Id |
| `department_id` | `any` | No | Department Id |
| `bed_id` | `any` | No | Bed Id |
| `admitted_at` | `string` | Yes | Admitted At |
| `discharged_at` | `any` | No | Discharged At |
| `reason` | `any` | No | Reason |
| `status` | `string` | Yes | Status |

### 7.AgentRouteRequest (`AgentRouteRequest`)
| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `capability` | `string` | Yes | Capability |

### 7.AppointmentCreate (`AppointmentCreate`)
| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `doctor_id` | `any` | No | Doctor Id |
| `specialist` | `string` | Yes | Specialist |
| `date` | `string` | Yes | Date |
| `time` | `string` | Yes | Time |
| `reason` | `string` | Yes | Reason |

### 7.AppointmentResponse (`AppointmentResponse`)
| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `id` | `integer` | Yes | Id |
| `facility_id` | `any` | No | Facility Id |
| `user_id` | `integer` | Yes | User Id |
| `doctor_id` | `any` | No | Doctor Id |
| `specialist` | `string` | Yes | Specialist |
| `date_time` | `string` | Yes | Date Time |
| `reason` | `string` | Yes | Reason |
| `status` | `string` | Yes | Status |

### 7.BIAskRequest (`BIAskRequest`)
| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `question` | `string` | Yes | Question |
| `table` | `any` | No | Table |

### 7.BedCreate (`BedCreate`)
| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `department_id` | `integer` | Yes | Department Id |
| `bed_number` | `string` | Yes | Bed Number |
| `ward` | `any` | No | Ward |
| `status` | `any` | No | Status |

### 7.BedResponse (`BedResponse`)
| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `id` | `integer` | Yes | Id |
| `facility_id` | `any` | No | Facility Id |
| `department_id` | `integer` | Yes | Department Id |
| `bed_number` | `string` | Yes | Bed Number |
| `ward` | `any` | No | Ward |
| `status` | `string` | Yes | Status |
| `current_patient_id` | `any` | No | Current Patient Id |
| `created_at` | `string` | Yes | Created At |

### 7.BedStatusUpdate (`BedStatusUpdate`)
> Schema for updating a bed's operational status.
| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `status` | `string` | Yes | Status |
| `current_patient_id` | `any` | No | Current Patient Id |

### 7.BillableServiceCreate (`BillableServiceCreate`)
| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `service_code` | `string` | Yes | Service Code |
| `name` | `string` | Yes | Name |
| `service_type` | `string` | Yes | Service Type |
| `department_id` | `any` | No | Department Id |
| `unit_price` | `number` | Yes | Unit Price |

### 7.BillableServiceResponse (`BillableServiceResponse`)
| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `service_code` | `string` | Yes | Service Code |
| `name` | `string` | Yes | Name |
| `service_type` | `string` | Yes | Service Type |
| `department_id` | `any` | No | Department Id |
| `unit_price` | `number` | Yes | Unit Price |
| `id` | `integer` | Yes | Id |
| `facility_id` | `any` | No | Facility Id |
| `status` | `string` | Yes | Status |
| `created_at` | `string` | Yes | Created At |

### 7.BillingPaymentCreate (`BillingPaymentCreate`)
| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `amount` | `number` | Yes | Amount |
| `payment_method` | `string` | Yes | Payment Method |
| `reference_id` | `any` | No | Reference Id |

### 7.Body_analyze_report_v1_analyze_report_post (`Body_analyze_report_v1_analyze_report_post`)
| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `file` | `string` | Yes | File |

### 7.Body_exchange_token_v1_smart_token_post (`Body_exchange_token_v1_smart_token_post`)
| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `grant_type` | `string` | Yes | Grant Type |
| `code` | `string` | Yes | Code |
| `redirect_uri` | `string` | Yes | Redirect Uri |
| `client_id` | `string` | Yes | Client Id |

### 7.Body_login_for_access_token_v1_token_post (`Body_login_for_access_token_v1_token_post`)
| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `totp_code` | `any` | No | Totp Code |
| `grant_type` | `any` | No | Grant Type |
| `username` | `string` | Yes | Username |
| `password` | `string` | Yes | Password |
| `scope` | `string` | No | Scope |
| `client_id` | `any` | No | Client Id |
| `client_secret` | `any` | No | Client Secret |

### 7.Body_transcribe_audio_v1_audio_transcribe_post (`Body_transcribe_audio_v1_audio_transcribe_post`)
| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `file` | `string` | Yes | File |

### 7.CASAChatRequest (`CASAChatRequest`)
| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `message` | `string` | Yes | Message |
| `history` | `List[CASAMessage]` | No | History |

### 7.CASAMessage (`CASAMessage`)
| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `role` | `string` | Yes | Role |
| `content` | `string` | Yes | Content |

### 7.CareEventCreate (`CareEventCreate`)
> Schema for creating a new care event (e.g. code-blue, nurse-call).
| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `patient_id` | `any` | No | Patient Id |
| `encounter_id` | `any` | No | Encounter Id |
| `department_id` | `any` | No | Department Id |
| `event_type` | `string` | Yes | Event Type |
| `title` | `string` | Yes | Title |
| `summary` | `any` | No | Summary |
| `severity` | `any` | No | Severity |

### 7.CareEventResponse (`CareEventResponse`)
| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `id` | `integer` | Yes | Id |
| `facility_id` | `any` | No | Facility Id |
| `patient_id` | `integer` | Yes | Patient Id |
| `actor_user_id` | `any` | No | Actor User Id |
| `encounter_id` | `any` | No | Encounter Id |
| `department_id` | `any` | No | Department Id |
| `event_type` | `string` | Yes | Event Type |
| `title` | `string` | Yes | Title |
| `summary` | `any` | No | Summary |
| `severity` | `string` | Yes | Severity |
| `created_at` | `string` | Yes | Created At |

### 7.ChatLogResponse (`ChatLogResponse`)
| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `id` | `integer` | Yes | Id |
| `role` | `string` | Yes | Role |
| `content` | `string` | Yes | Content |
| `timestamp` | `string` | Yes | Timestamp |

### 7.ChatRequest (`ChatRequest`)
| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `message` | `string` | Yes | Message |
| `history` | `List[Message]` | No | History |
| `current_context` | `object` | No | Current Context |
| `model` | `any` | No | Model |
| `language` | `any` | No | Language |

### 7.ClinicalAlertResponse (`ClinicalAlertResponse`)
> Serialised clinical alert.
| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `id` | `integer` | Yes | Id |
| `patient_id` | `integer` | Yes | Patient Id |
| `alert_type` | `string` | Yes | Alert Type |
| `severity` | `string` | Yes | Severity |
| `message` | `string` | Yes | Message |
| `source_event_id` | `any` | No | Source Event Id |
| `is_acknowledged` | `boolean` | Yes | Is Acknowledged |
| `acknowledged_by` | `any` | No | Acknowledged By |
| `acknowledged_at` | `any` | No | Acknowledged At |
| `created_at` | `string` | Yes | Created At |

### 7.ClinicalCouncilConsensusResponse (`ClinicalCouncilConsensusResponse`)
> Final unified consensus synthesized by the medical council.
| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `patient_id` | `string` | Yes | Patient Id |
| `council_session_id` | `string` | Yes | Council Session Id |
| `consensus_diagnosis` | `string` | Yes | Consensus Diagnosis |
| `consensus_confidence` | `number` | Yes | Consensus Confidence |
| `specialist_opinions` | `List[SpecialistOpinion]` | Yes | Specialist Opinions |
| `unified_care_plan` | `List[string]` | Yes | Unified Care Plan |
| `critical_safety_alerts` | `List[string]` | Yes | Critical Safety Alerts |
| `medical_disclaimer` | `string` | No | Medical Disclaimer |

### 7.ClinicalCouncilDeliberationRequest (`ClinicalCouncilDeliberationRequest`)
> Request for autonomous multi-specialist medical council deliberation.
| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `patient_id` | `string` | Yes | Patient Id |
| `clinical_summary` | `string` | Yes | Clinical Summary |
| `primary_symptoms` | `List[string]` | Yes | Primary Symptoms |
| `vitals_summary` | `object` | Yes | Vitals Summary |
| `lab_results` | `object` | Yes | Lab Results |
| `current_medications` | `List[string]` | Yes | Current Medications |

### 7.ClinicalOrderCreate (`ClinicalOrderCreate`)
| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `encounter_id` | `any` | No | Encounter Id |
| `patient_id` | `integer` | Yes | Patient Id |
| `doctor_id` | `any` | No | Doctor Id |
| `department_id` | `any` | No | Department Id |
| `order_type` | `string` | Yes | Order Type |
| `title` | `string` | Yes | Title |
| `priority` | `any` | No | Priority |
| `notes` | `any` | No | Notes |

### 7.ClinicalOrderResponse (`ClinicalOrderResponse`)
| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `id` | `integer` | Yes | Id |
| `facility_id` | `any` | No | Facility Id |
| `encounter_id` | `any` | No | Encounter Id |
| `patient_id` | `integer` | Yes | Patient Id |
| `doctor_id` | `any` | No | Doctor Id |
| `department_id` | `any` | No | Department Id |
| `order_type` | `string` | Yes | Order Type |
| `title` | `string` | Yes | Title |
| `priority` | `string` | Yes | Priority |
| `status` | `string` | Yes | Status |
| `notes` | `any` | No | Notes |
| `created_at` | `string` | Yes | Created At |
| `completed_at` | `any` | No | Completed At |

### 7.ClinicianOverrideRequest (`ClinicianOverrideRequest`)
| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `patient_id` | `integer` | Yes | Patient Id |
| `function_name` | `string` | Yes | Function Name |
| `original_ai_output` | `string` | Yes | Original Ai Output |
| `corrected_output` | `any` | No | Corrected Output |
| `override_action` | `string` | Yes | Override Action |
| `override_reason` | `any` | No | Override Reason |

### 7.CompactRequest (`CompactRequest`)
| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `fhir_bundle` | `object` | Yes | Fhir Bundle |

### 7.ConsentAcceptRequest (`ConsentAcceptRequest`)
| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `eula_version` | `string` | No | Eula Version |

### 7.ConsentArtifactCreate (`ConsentArtifactCreate`)
| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `patient_abha` | `string` | Yes | Patient Abha |
| `purpose` | `string` | No | Purpose |
| `hi_types` | `List[string]` | No | Hi Types |
| `valid_until` | `string` | No | Valid Until |

### 7.ConsentArtifactResponse (`ConsentArtifactResponse`)
| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `consent_id` | `string` | Yes | Consent Id |
| `patient_abha` | `string` | Yes | Patient Abha |
| `status` | `string` | Yes | Status |
| `purpose` | `string` | Yes | Purpose |
| `hi_types` | `List[string]` | No | Hi Types |
| `granted_at` | `string` | Yes | Granted At |
| `valid_until` | `string` | Yes | Valid Until |

### 7.CounterfactualRequest (`CounterfactualRequest`)
| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `target_model` | `string` | Yes | Target Model |
| `features` | `object` | Yes | Features |

### 7.DecompressRequest (`DecompressRequest`)
| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `compressed_data` | `string` | Yes | Compressed Data |

### 7.DeleteModelRequest (`DeleteModelRequest`)
| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `name` | `string` | Yes | Name |

### 7.DepartmentCreate (`DepartmentCreate`)
| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `facility_id` | `any` | No | Facility Id |
| `name` | `string` | Yes | Name |
| `department_type` | `string` | Yes | Department Type |
| `location` | `any` | No | Location |
| `description` | `any` | No | Description |

### 7.DepartmentResponse (`DepartmentResponse`)
| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `facility_id` | `any` | No | Facility Id |
| `name` | `string` | Yes | Name |
| `department_type` | `string` | Yes | Department Type |
| `location` | `any` | No | Location |
| `description` | `any` | No | Description |
| `id` | `integer` | Yes | Id |
| `status` | `string` | Yes | Status |
| `created_at` | `string` | Yes | Created At |

### 7.DiabetesInput (`DiabetesInput`)
> Schema for Diabetes Prediction (BRFSS 2015 Big Data)
| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `gender` | `any` | No | 0: Female, 1: Male |
| `age` | `any` | No | Age in years |
| `hypertension` | `any` | No | 0: No, 1: Yes |
| `heart_disease` | `any` | No | 0: No, 1: Yes |
| `smoking_history` | `any` | No | 0: No, 1: Yes |
| `bmi` | `any` | No | Body Mass Index |
| `high_chol` | `any` | No | 0: No, 1: Yes |
| `physical_activity` | `any` | No | 0: No, 1: Yes (Past 30 days) |
| `general_health` | `any` | No | 1 (Excellent) to 5 (Poor) |

### 7.DiabetesVisit (`DiabetesVisit`)
> Single clinical visit record for diabetes risk features.
| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `gender` | `any` | No | 0: Female, 1: Male |
| `age` | `any` | No | Age in years at time of visit |
| `hypertension` | `any` | No | 0: No, 1: Yes |
| `heart_disease` | `any` | No | 0: No, 1: Yes |
| `smoking_history` | `any` | No | 0: No, 1: Yes |
| `bmi` | `any` | No | Body Mass Index |
| `high_chol` | `any` | No | 0: No, 1: Yes |
| `physical_activity` | `any` | No | 0: No, 1: Yes (Past 30 days) |
| `general_health` | `any` | No | 1 (Excellent) to 5 (Poor) |

### 7.DiagnosticResultCreate (`DiagnosticResultCreate`)
| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `order_id` | `integer` | Yes | Order Id |
| `result_type` | `string` | Yes | Result Type |
| `title` | `string` | Yes | Title |
| `summary` | `string` | Yes | Summary |
| `abnormal_flag` | `any` | No | Abnormal Flag |
| `status` | `any` | No | Status |

### 7.DiagnosticResultResponse (`DiagnosticResultResponse`)
| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `id` | `integer` | Yes | Id |
| `facility_id` | `any` | No | Facility Id |
| `order_id` | `integer` | Yes | Order Id |
| `encounter_id` | `any` | No | Encounter Id |
| `patient_id` | `integer` | Yes | Patient Id |
| `doctor_id` | `any` | No | Doctor Id |
| `department_id` | `any` | No | Department Id |
| `result_type` | `string` | Yes | Result Type |
| `title` | `string` | Yes | Title |
| `summary` | `string` | Yes | Summary |
| `abnormal_flag` | `boolean` | Yes | Abnormal Flag |
| `status` | `string` | Yes | Status |
| `review_status` | `string` | Yes | Review Status |
| `review_note` | `any` | No | Review Note |
| `reviewed_by_id` | `any` | No | Reviewed By Id |
| `reviewed_at` | `any` | No | Reviewed At |
| `created_at` | `string` | Yes | Created At |

### 7.DiagnosticReviewUpdate (`DiagnosticReviewUpdate`)
| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `review_status` | `any` | No | Review Status |
| `review_note` | `any` | No | Review Note |

### 7.DiagnosticUploadCreate (`DiagnosticUploadCreate`)
| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `patient_id` | `integer` | Yes | Patient Id |
| `title` | `string` | Yes | Title |
| `result_type` | `any` | No | Result Type |
| `summary` | `any` | No | Summary |
| `abnormal_flag` | `any` | No | Abnormal Flag |

### 7.DigitalTwinSimulationRequest (`DigitalTwinSimulationRequest`)
> Request to simulate 10-year clinical trajectory on a patient's digital twin.
| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `patient_id` | `string` | Yes | Patient Id |
| `age` | `number` | Yes | Age |
| `gender` | `string` | No | Gender |
| `bmi` | `number` | No | Bmi |
| `systolic_bp` | `number` | No | Systolic Bp |
| `fasting_glucose` | `number` | No | Fasting Glucose |
| `egfr` | `number` | No | Egfr |
| `ldl_cholesterol` | `number` | No | Ldl Cholesterol |
| `hba1c` | `number` | No | Hba1C |
| `smoking_status` | `string` | No | Smoking Status |
| `active_diagnoses` | `List[string]` | No | Active Diagnoses |
| `proposed_interventions` | `List[string]` | No | List of proposed pharmacological or lifestyle interventions |

### 7.DigitalTwinSimulationResponse (`DigitalTwinSimulationResponse`)
> Full 10-year multi-organ digital twin simulation output.
| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `patient_id` | `string` | Yes | Patient Id |
| `simulation_horizon_years` | `integer` | No | Simulation Horizon Years |
| `cardiovascular` | `OrganSystemTrajectory` | Yes |  |
| `renal` | `OrganSystemTrajectory` | Yes |  |
| `metabolic` | `OrganSystemTrajectory` | Yes |  |
| `hepatic` | `OrganSystemTrajectory` | Yes |  |
| `overall_longevity_gain_years` | `number` | Yes | Estimated quality-adjusted life years (QALY) gained |
| `top_recommended_pathway` | `string` | Yes | Top Recommended Pathway |
| `simulation_confidence_interval` | `string` | No | Simulation Confidence Interval |

### 7.DischargeSummaryCreate (`DischargeSummaryCreate`)
| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `admission_id` | `integer` | Yes | Admission Id |
| `encounter_id` | `any` | No | Encounter Id |
| `patient_id` | `integer` | Yes | Patient Id |
| `doctor_id` | `any` | No | Doctor Id |
| `diagnosis_summary` | `string` | Yes | Diagnosis Summary |
| `hospital_course` | `string` | Yes | Hospital Course |
| `medications` | `any` | No | Medications |
| `follow_up_plan` | `any` | No | Follow Up Plan |
| `discharge_instructions` | `any` | No | Discharge Instructions |

### 7.DischargeSummaryResponse (`DischargeSummaryResponse`)
| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `id` | `integer` | Yes | Id |
| `facility_id` | `any` | No | Facility Id |
| `admission_id` | `integer` | Yes | Admission Id |
| `encounter_id` | `any` | No | Encounter Id |
| `patient_id` | `integer` | Yes | Patient Id |
| `doctor_id` | `any` | No | Doctor Id |
| `diagnosis_summary` | `string` | Yes | Diagnosis Summary |
| `hospital_course` | `string` | Yes | Hospital Course |
| `medications` | `any` | No | Medications |
| `follow_up_plan` | `any` | No | Follow Up Plan |
| `discharge_instructions` | `any` | No | Discharge Instructions |
| `status` | `string` | Yes | Status |
| `created_at` | `string` | Yes | Created At |
| `finalized_at` | `any` | No | Finalized At |

### 7.DispenseItemCreate (`DispenseItemCreate`)
| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `prescription_item_id` | `integer` | Yes | Prescription Item Id |
| `quantity_dispensed` | `number` | Yes | Quantity Dispensed |

### 7.DispensePrescriptionCreate (`DispensePrescriptionCreate`)
| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `items` | `List[DispenseItemCreate]` | Yes | Items |

### 7.DoctorResponse (`DoctorResponse`)
| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `id` | `integer` | Yes | Id |
| `full_name` | `string` | Yes | Full Name |
| `specialization` | `string` | No | Specialization |
| `consultation_fee` | `number` | Yes | Consultation Fee |
| `profile_picture` | `any` | No | Profile Picture |

### 7.DrugMetabolismReport (`DrugMetabolismReport`)
> Precision metabolism and dosage adjustment report for a specific drug.
| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `drug_name` | `string` | Yes | Drug Name |
| `relevant_gene` | `string` | Yes | Relevant Gene |
| `metabolic_status` | `string` | Yes | Metabolic Status |
| `clinical_implication` | `string` | Yes | Clinical Implication |
| `recommended_dosage_adjustment` | `string` | Yes | Recommended Dosage Adjustment |
| `adverse_reaction_risk` | `string` | Yes | Adverse Reaction Risk |
| `cpic_guideline_level` | `string` | No | Cpic Guideline Level |

### 7.DrugSafetyCheckRequest (`DrugSafetyCheckRequest`)
| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `patient_id` | `integer` | Yes | Patient Id |
| `medication_name` | `string` | Yes | Medication Name |
| `dosage` | `string` | Yes | Dosage |
| `frequency` | `string` | Yes | Frequency |
| `duration` | `string` | Yes | Duration |
| `additional_allergies` | `any` | No | Additional Allergies |

### 7.EncounterCreate (`EncounterCreate`)
| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `patient_id` | `integer` | Yes | Patient Id |
| `doctor_id` | `any` | No | Doctor Id |
| `department_id` | `any` | No | Department Id |
| `encounter_type` | `string` | Yes | Encounter Type |
| `reason` | `any` | No | Reason |
| `priority` | `any` | No | Priority |

### 7.EncounterResponse (`EncounterResponse`)
| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `id` | `integer` | Yes | Id |
| `facility_id` | `any` | No | Facility Id |
| `patient_id` | `integer` | Yes | Patient Id |
| `doctor_id` | `any` | No | Doctor Id |
| `department_id` | `any` | No | Department Id |
| `encounter_type` | `string` | Yes | Encounter Type |
| `reason` | `any` | No | Reason |
| `priority` | `string` | Yes | Priority |
| `status` | `string` | Yes | Status |
| `started_at` | `string` | Yes | Started At |
| `ended_at` | `any` | No | Ended At |

### 7.ExplainabilityResponse (`ExplainabilityResponse`)
> SHAP-style feature-importance explanation for a prediction.
| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `prediction_id` | `integer` | Yes | Prediction Id |
| `model_name` | `string` | Yes | Model Name |
| `feature_importances` | `object` | Yes | Feature Importances |
| `explanation_text` | `string` | Yes | Explanation Text |

### 7.ExplanationResponse (`ExplanationResponse`)
| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `explanation` | `string` | Yes | Explanation |
| `lifestyle_tips` | `List[string]` | Yes | Lifestyle Tips |

### 7.FacilityCreate (`FacilityCreate`)
| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `name` | `string` | Yes | Name |
| `facility_type` | `string` | No | Facility Type |
| `country` | `any` | No | Country |
| `region` | `any` | No | Region |

### 7.FacilityResponse (`FacilityResponse`)
| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `name` | `string` | Yes | Name |
| `facility_type` | `string` | No | Facility Type |
| `country` | `any` | No | Country |
| `region` | `any` | No | Region |
| `id` | `integer` | Yes | Id |
| `status` | `string` | Yes | Status |
| `created_at` | `string` | Yes | Created At |

### 7.FederatedSyncAuditResponse (`FederatedSyncAuditResponse`)
> Serialised sync audit record.
| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `id` | `integer` | Yes | Id |
| `sync_run_id` | `string` | Yes | Sync Run Id |
| `node_id` | `string` | Yes | Node Id |
| `model_name` | `string` | Yes | Model Name |
| `records_synced` | `integer` | Yes | Records Synced |
| `epsilon_consumed` | `number` | Yes | Epsilon Consumed |
| `delta_consumed` | `number` | Yes | Delta Consumed |
| `status` | `string` | Yes | Status |
| `error_message` | `any` | No | Error Message |
| `created_at` | `string` | Yes | Created At |

### 7.FederatedSyncRequest (`FederatedSyncRequest`)
> Parameters for a differential-privacy federated sync.
| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `model_name` | `string` | Yes | Model Name |
| `epsilon` | `number` | No | Epsilon |
| `sensitivity` | `number` | No | Sensitivity |

### 7.FederatedSyncResponse (`FederatedSyncResponse`)
> Result of a federated DP sync run.
| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `sync_run_id` | `string` | Yes | Sync Run Id |
| `records_synced` | `integer` | Yes | Records Synced |
| `epsilon_consumed` | `number` | Yes | Epsilon Consumed |
| `noisy_gradients` | `object` | Yes | Noisy Gradients |
| `status` | `string` | Yes | Status |

### 7.FeedbackEvent (`FeedbackEvent`)
> Feedback event for Thompson Sampling bandit learning and delayed outcome tracking.
| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `patient_id` | `string` | Yes | Patient Id |
| `item_id` | `string` | Yes | Item Id |
| `action` | `string` | Yes | Action: impression, click, accept, decline, completed |
| `outcome_value` | `number` | No | Reward signal (1.0 for positive, 0.0 for negative) |
| `time_delay_hours` | `any` | No | Time elapsed before outcome observed |

### 7.ForgotPasswordRequest (`ForgotPasswordRequest`)
> Schema for password reset request
| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `email` | `string` | Yes | Email |

### 7.FourEyeActionType (`FourEyeActionType`)
Type: `string`

### 7.FourEyeCheckRequest (`FourEyeCheckRequest`)
| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `request_id` | `string` | Yes | Request Id |
| `action_type` | `FourEyeActionType` | Yes |  |
| `patient_id` | `integer` | Yes | Patient Id |
| `initiator_doctor_id` | `integer` | Yes | Initiator Doctor Id |
| `initiator_doctor_name` | `string` | Yes | Initiator Doctor Name |
| `initiator_npi` | `string` | Yes | Initiator Npi |
| `clinical_justification` | `string` | Yes | Clinical Justification |
| `payload` | `object` | Yes | Payload |
| `created_at` | `string` | Yes | Created At |
| `status` | `FourEyeStatus` | No |  |
| `reviewer_doctor_id` | `any` | No | Reviewer Doctor Id |
| `reviewer_doctor_name` | `any` | No | Reviewer Doctor Name |
| `reviewer_npi` | `any` | No | Reviewer Npi |
| `reviewer_comments` | `any` | No | Reviewer Comments |
| `reviewed_at` | `any` | No | Reviewed At |
| `cryptographic_hmac` | `string` | No | Cryptographic Hmac |

### 7.FourEyeReviewPayload (`FourEyeReviewPayload`)
| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `request_id` | `string` | Yes | Request Id |
| `approved` | `boolean` | Yes | Approved |
| `comments` | `string` | Yes | Comments |
| `reviewer_npi` | `any` | No | Reviewer Npi |

### 7.FourEyeStatus (`FourEyeStatus`)
Type: `string`

### 7.FourEyeSubmitPayload (`FourEyeSubmitPayload`)
| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `action_type` | `FourEyeActionType` | Yes |  |
| `patient_id` | `integer` | Yes | Patient Id |
| `clinical_justification` | `string` | Yes | Clinical Justification |
| `payload` | `object` | Yes | Payload |

### 7.GovernanceCheckResult (`GovernanceCheckResult`)
| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `is_safe` | `boolean` | Yes | Is Safe |
| `passed_levels` | `List[string]` | Yes | Passed Levels |
| `failed_level` | `any` | No | Failed Level |
| `risk_score` | `number` | No | Risk Score |
| `action_required` | `string` | No | Action Required |
| `four_eye_request_id` | `any` | No | Four Eye Request Id |
| `sanitized_content` | `string` | No | Sanitized Content |
| `governance_metadata` | `object` | No | Governance Metadata |

### 7.HTTPValidationError (`HTTPValidationError`)
| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `detail` | `List[ValidationError]` | No | Detail |

### 7.HealthRecordResponse (`HealthRecordResponse`)
| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `id` | `integer` | Yes | Id |
| `record_type` | `string` | Yes | Record Type |
| `prediction` | `string` | Yes | Prediction |
| `timestamp` | `string` | Yes | Timestamp |
| `data` | `string` | Yes | Data |

### 7.HeartInput (`HeartInput`)
> Schema for Heart Disease Prediction (Cleveland Dataset).
Feature Logic: Focuses on Lab Reports and Clinical Vitals.
| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `age` | `any` | No | Age in years. |
| `sex` | `any` | No | 0: Female, 1: Male |
| `cp` | `any` | No | Chest pain type (0-3) |
| `trestbps` | `any` | No | Resting blood pressure |
| `chol` | `any` | No | Serum cholesterol in mg/dl |
| `fbs` | `any` | No | Fasting blood sugar > 120 mg/dl (1/0) |
| `restecg` | `any` | No | Resting ECG results (0-2) |
| `thalach` | `any` | No | Maximum heart rate achieved |
| `exang` | `any` | No | Exercise induced angina (1/0) |
| `oldpeak` | `any` | No | ST depression induced by exercise |
| `slope` | `any` | No | Slope of the peak exercise ST segment (0-2) |
| `ca` | `any` | No | Number of major vessels (0-4) |
| `thal` | `any` | No | Thalassemia (1-3) |
| `hdl` | `any` | No | HDL Cholesterol in mg/dL (Default: 50.0) |
| `smoker` | `any` | No | 0: Non-smoker, 1: Smoker (Default: 0) |
| `hyp_treatment` | `any` | No | 0: Untreated, 1: Treated (Default: 0) |

### 7.HeartVisit (`HeartVisit`)
> Single clinical visit record for heart disease risk features.
| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `age` | `any` | No | Age in years |
| `sex` | `any` | No | 0: Female, 1: Male |
| `cp` | `any` | No | Chest pain type (0-3) |
| `trestbps` | `any` | No | Resting blood pressure |
| `chol` | `any` | No | Serum cholesterol in mg/dl |
| `fbs` | `any` | No | Fasting blood sugar > 120 mg/dl (1/0) |
| `restecg` | `any` | No | Resting ECG results (0-2) |
| `thalach` | `any` | No | Maximum heart rate achieved |
| `exang` | `any` | No | Exercise induced angina (1/0) |
| `oldpeak` | `any` | No | ST depression induced by exercise |
| `slope` | `any` | No | Slope of the peak exercise ST segment (0-2) |
| `ca` | `any` | No | Number of major vessels (0-4) |
| `thal` | `any` | No | Thalassemia (1-3) |

### 7.InteroperabilityConsentCreate (`InteroperabilityConsentCreate`)
| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `scope` | `string` | No | Scope |
| `purpose` | `string` | Yes | Purpose |
| `recipient_type` | `string` | No | Recipient Type |
| `expires_at` | `any` | No | Expires At |

### 7.InteroperabilityExportProfileCreate (`InteroperabilityExportProfileCreate`)
| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `name` | `string` | Yes | Name |
| `partner_system` | `any` | No | Partner System |
| `resource_types` | `any` | No | Resource Types |
| `department_id` | `any` | No | Department Id |
| `status` | `any` | No | Status |

### 7.InvoiceCreate (`InvoiceCreate`)
| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `patient_id` | `integer` | Yes | Patient Id |
| `encounter_id` | `any` | No | Encounter Id |
| `admission_id` | `any` | No | Admission Id |
| `discount_amount` | `number` | No | Discount Amount |
| `tax_amount` | `number` | No | Tax Amount |
| `currency` | `any` | No | Currency |
| `items` | `List[InvoiceLineItemCreate]` | Yes | Items |

### 7.InvoiceLineItemCreate (`InvoiceLineItemCreate`)
| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `service_id` | `any` | No | Service Id |
| `description` | `any` | No | Description |
| `quantity` | `number` | No | Quantity |
| `unit_price` | `any` | No | Unit Price |

### 7.InvoiceLineItemResponse (`InvoiceLineItemResponse`)
| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `id` | `integer` | Yes | Id |
| `invoice_id` | `integer` | Yes | Invoice Id |
| `service_id` | `any` | No | Service Id |
| `description` | `string` | Yes | Description |
| `quantity` | `number` | Yes | Quantity |
| `unit_price` | `number` | Yes | Unit Price |
| `line_total` | `number` | Yes | Line Total |

### 7.InvoiceResponse (`InvoiceResponse`)
| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `id` | `integer` | Yes | Id |
| `facility_id` | `any` | No | Facility Id |
| `patient_id` | `integer` | Yes | Patient Id |
| `encounter_id` | `any` | No | Encounter Id |
| `admission_id` | `any` | No | Admission Id |
| `created_by_id` | `any` | No | Created By Id |
| `status` | `string` | Yes | Status |
| `subtotal` | `number` | Yes | Subtotal |
| `discount_amount` | `number` | Yes | Discount Amount |
| `tax_amount` | `number` | Yes | Tax Amount |
| `total_amount` | `number` | Yes | Total Amount |
| `paid_amount` | `number` | Yes | Paid Amount |
| `balance_amount` | `number` | Yes | Balance Amount |
| `currency` | `string` | Yes | Currency |
| `created_at` | `string` | Yes | Created At |
| `issued_at` | `string` | Yes | Issued At |
| `items` | `List[InvoiceLineItemResponse]` | No | Items |

### 7.KidneyInput (`KidneyInput`)
> Schema for Kidney Disease Prediction (24 Features).
| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `age` | `any` | No | Age |
| `bp` | `any` | No | Bp |
| `sg` | `any` | No | Sg |
| `al` | `any` | No | Al |
| `su` | `any` | No | Su |
| `rbc` | `any` | No | Rbc |
| `pc` | `any` | No | Pc |
| `pcc` | `any` | No | Pcc |
| `ba` | `any` | No | Ba |
| `bgr` | `any` | No | Bgr |
| `bu` | `any` | No | Bu |
| `sc` | `any` | No | Sc |
| `sod` | `any` | No | Sod |
| `pot` | `any` | No | Pot |
| `hemo` | `any` | No | Hemo |
| `pcv` | `any` | No | Pcv |
| `wc` | `any` | No | Wc |
| `rc` | `any` | No | Rc |
| `htn` | `any` | No | Htn |
| `dm` | `any` | No | Dm |
| `cad` | `any` | No | Cad |
| `appet` | `any` | No | Appet |
| `pe` | `any` | No | Pe |
| `ane` | `any` | No | Ane |
| `gender` | `any` | No | 0: Female, 1: Male (Default: 1) |

### 7.KidneyVisit (`KidneyVisit`)
> Single clinical visit record for kidney disease risk features.
| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `age` | `any` | No | Age |
| `blood_pressure` | `any` | No | Blood Pressure |
| `specific_gravity` | `any` | No | Specific Gravity |
| `albumin` | `any` | No | Albumin |
| `sugar` | `any` | No | Sugar |
| `blood_glucose_random` | `any` | No | Blood Glucose Random |
| `blood_urea` | `any` | No | Blood Urea |
| `serum_creatinine` | `any` | No | Serum Creatinine |
| `sodium` | `any` | No | Sodium |
| `potassium` | `any` | No | Potassium |
| `hemoglobin` | `any` | No | Hemoglobin |
| `packed_cell_volume` | `any` | No | Packed Cell Volume |
| `white_blood_cell_count` | `any` | No | White Blood Cell Count |
| `red_blood_cell_count` | `any` | No | Red Blood Cell Count |
| `hypertension` | `any` | No | Hypertension |
| `diabetes_mellitus` | `any` | No | Diabetes Mellitus |
| `appetite` | `any` | No | Appetite |
| `pedal_edema` | `any` | No | Pedal Edema |
| `anemia` | `any` | No | Anemia |

### 7.LabKitOrderRequest (`LabKitOrderRequest`)
| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `patient_id` | `integer` | Yes | Patient Id |
| `kit_type` | `string` | Yes | Kit Type |
| `shipping_address` | `string` | Yes | Shipping Address |

### 7.LicenseActivationPayload (`LicenseActivationPayload`)
| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `license_key` | `string` | Yes | License Key |

### 7.LiverInput (`LiverInput`)
> Schema for Liver Disease Prediction (ILPD).
| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `age` | `any` | No | Age |
| `gender` | `any` | No | Gender |
| `total_bilirubin` | `any` | No | Total Bilirubin |
| `direct_bilirubin` | `any` | No | Direct Bilirubin |
| `alkaline_phosphotase` | `any` | No | Alkaline Phosphotase |
| `alamine_aminotransferase` | `any` | No | Alamine Aminotransferase |
| `aspartate_aminotransferase` | `any` | No | Aspartate Aminotransferase |
| `total_proteins` | `any` | No | Total Proteins |
| `albumin` | `any` | No | Albumin |
| `albumin_and_globulin_ratio` | `any` | No | Albumin And Globulin Ratio |
| `platelets` | `any` | No | Platelets in 10^9/L (Default: 250.0) |

### 7.LiverVisit (`LiverVisit`)
> Single clinical visit record for liver disease risk features.
| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `age` | `any` | No | Age |
| `gender` | `any` | No | Gender |
| `total_bilirubin` | `any` | No | Total Bilirubin |
| `direct_bilirubin` | `any` | No | Direct Bilirubin |
| `alkaline_phosphotase` | `any` | No | Alkaline Phosphotase |
| `alamine_aminotransferase` | `any` | No | Alamine Aminotransferase |
| `aspartate_aminotransferase` | `any` | No | Aspartate Aminotransferase |
| `total_proteins` | `any` | No | Total Proteins |
| `albumin` | `any` | No | Albumin |
| `albumin_globulin_ratio` | `any` | No | Albumin Globulin Ratio |

### 7.LongitudinalDiabetesRequest (`LongitudinalDiabetesRequest`)
> Sequence of diabetes visits for temporal risk prediction.
| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `patient_id` | `any` | No | Patient ID for audit trail |
| `visits` | `List[DiabetesVisit]` | Yes | Chronological list of diabetes visit records (oldest → newest). Minimum 2 visits required. |

### 7.LongitudinalHeartRequest (`LongitudinalHeartRequest`)
> Sequence of heart visits for temporal risk prediction.
| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `patient_id` | `any` | No | Patient ID for audit trail |
| `visits` | `List[HeartVisit]` | Yes | Chronological list of heart visit records (oldest → newest). Minimum 2 visits required. |

### 7.LongitudinalKidneyRequest (`LongitudinalKidneyRequest`)
> Sequence of kidney visits for temporal risk prediction.
| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `patient_id` | `any` | No | Patient ID for audit trail |
| `visits` | `List[KidneyVisit]` | Yes | Chronological list of kidney visit records (oldest → newest). Minimum 2 visits required. |

### 7.LongitudinalLiverRequest (`LongitudinalLiverRequest`)
> Sequence of liver visits for temporal risk prediction.
| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `patient_id` | `any` | No | Patient ID for audit trail |
| `visits` | `List[LiverVisit]` | Yes | Chronological list of liver visit records (oldest → newest). Minimum 2 visits required. |

### 7.LongitudinalPredictionResponse (`LongitudinalPredictionResponse`)
> Response from longitudinal temporal prediction endpoints.
| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `condition` | `string` | Yes | Disease domain (diabetes, heart, liver, kidney) |
| `risk_probability` | `number` | Yes | Predicted positive-class probability |
| `risk_label` | `string` | Yes | LOW / MODERATE / HIGH / VERY HIGH |
| `trend` | `string` | Yes | IMPROVING / STABLE / WORSENING based on visit trajectory |
| `num_visits` | `integer` | Yes | Number of visits in the input sequence |
| `visit_attention` | `List[VisitAttention]` | Yes | Per-visit attention weights showing which visits influenced the prediction most |
| `medical_disclaimer` | `string` | Yes | Required medical disclaimer for AI-generated health advice |

### 7.LungInput (`LungInput`)
> Schema for Respiratory/Lung Health.
| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `gender` | `any` | No | Gender |
| `age` | `any` | No | Age |
| `smoking` | `any` | No | Smoking |
| `yellow_fingers` | `any` | No | Yellow Fingers |
| `anxiety` | `any` | No | Anxiety |
| `peer_pressure` | `any` | No | Peer Pressure |
| `chronic_disease` | `any` | No | Chronic Disease |
| `fatigue` | `any` | No | Fatigue |
| `allergy` | `any` | No | Allergy |
| `wheezing` | `any` | No | Wheezing |
| `alcohol` | `any` | No | Alcohol |
| `coughing` | `any` | No | Coughing |
| `shortness_of_breath` | `any` | No | Shortness Of Breath |
| `swallowing_difficulty` | `any` | No | Swallowing Difficulty |
| `chest_pain` | `any` | No | Chest Pain |

### 7.MedicationInventoryCreate (`MedicationInventoryCreate`)
| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `medication_name` | `string` | Yes | Medication Name |
| `strength` | `any` | No | Strength |
| `form` | `any` | No | Form |
| `batch_number` | `any` | No | Batch Number |
| `quantity_on_hand` | `number` | No | Quantity On Hand |
| `reorder_level` | `number` | No | Reorder Level |

### 7.MedicationInventoryResponse (`MedicationInventoryResponse`)
| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `medication_name` | `string` | Yes | Medication Name |
| `strength` | `any` | No | Strength |
| `form` | `any` | No | Form |
| `batch_number` | `any` | No | Batch Number |
| `quantity_on_hand` | `number` | No | Quantity On Hand |
| `reorder_level` | `number` | No | Reorder Level |
| `id` | `integer` | Yes | Id |
| `facility_id` | `any` | No | Facility Id |
| `status` | `string` | Yes | Status |
| `created_at` | `string` | Yes | Created At |

### 7.MeshPipelineRunRequest (`MeshPipelineRunRequest`)
| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `cohort_id` | `string` | No | Cohort Id |
| `patient_batch_size` | `integer` | No | Patient Batch Size |
| `enable_kaggle_gpu` | `boolean` | No | Enable Kaggle Gpu |
| `enable_databricks_lakehouse` | `boolean` | No | Enable Databricks Lakehouse |
| `enable_cloudflare_ai` | `boolean` | No | Enable Cloudflare Ai |
| `enable_hf_sync` | `boolean` | No | Enable Hf Sync |
| `enable_neon_export` | `boolean` | No | Enable Neon Export |

### 7.MeshPipelineRunResult (`MeshPipelineRunResult`)
| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `run_id` | `string` | Yes | Run Id |
| `cohort_id` | `string` | Yes | Cohort Id |
| `status` | `string` | Yes | Status |
| `total_duration_sec` | `number` | Yes | Total Duration Sec |
| `service_statuses` | `object` | Yes | Service Statuses |
| `summary` | `object` | Yes | Summary |
| `hipaa_audit_trail_id` | `string` | Yes | Hipaa Audit Trail Id |

### 7.MeshServiceStatus (`MeshServiceStatus`)
| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `service_name` | `string` | Yes | Service Name |
| `is_connected` | `boolean` | Yes | Is Connected |
| `latency_ms` | `number` | Yes | Latency Ms |
| `mode` | `string` | No | Mode |
| `message` | `string` | Yes | Message |
| `details` | `object` | No | Details |

### 7.Message (`Message`)
| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `role` | `string` | Yes | Role |
| `content` | `string` | Yes | Content |

### 7.ModelFeedbackCreate (`ModelFeedbackCreate`)
> Clinician submits a correction for a model prediction.
| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `patient_id` | `integer` | Yes | Patient Id |
| `model_name` | `string` | Yes | Model Name |
| `input_features` | `object` | Yes | Input Features |
| `prediction_result` | `object` | Yes | Prediction Result |
| `corrected_label` | `string` | Yes | Corrected Label |

### 7.ModelFeedbackResponse (`ModelFeedbackResponse`)
> Serialised feedback record.
| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `id` | `integer` | Yes | Id |
| `patient_id` | `integer` | Yes | Patient Id |
| `model_name` | `string` | Yes | Model Name |
| `input_features` | `string` | Yes | Input Features |
| `prediction_result` | `string` | Yes | Prediction Result |
| `corrected_label` | `string` | Yes | Corrected Label |
| `clinician_id` | `integer` | Yes | Clinician Id |
| `status` | `string` | Yes | Status |
| `created_at` | `string` | Yes | Created At |

### 7.MonitoringSignalResponse (`MonitoringSignalResponse`)
| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `id` | `integer` | Yes | Id |
| `facility_id` | `any` | No | Facility Id |
| `patient_id` | `integer` | Yes | Patient Id |
| `vital_observation_id` | `any` | No | Vital Observation Id |
| `encounter_id` | `any` | No | Encounter Id |
| `department_id` | `any` | No | Department Id |
| `signal_type` | `string` | Yes | Signal Type |
| `severity` | `string` | Yes | Severity |
| `title` | `string` | Yes | Title |
| `summary` | `string` | Yes | Summary |
| `status` | `string` | Yes | Status |
| `created_at` | `string` | Yes | Created At |

### 7.MultiOrganInput (`MultiOrganInput`)
> Unified schema for Multi-Organ Risk Assessment (union of all 5 inputs)
| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `gender` | `any` | No | 0: Female, 1: Male |
| `age` | `any` | No | Age in years |
| `smoking` | `any` | No | 0: No, 1: Yes |
| `physical_activity` | `any` | No | 0: No, 1: Yes |
| `alcohol` | `any` | No | 0: No, 1: Yes |
| `general_health` | `any` | No | 1 (Excellent) to 5 (Poor) |
| `bmi` | `any` | No | Body Mass Index |
| `glucose` | `any` | No | Blood glucose level |
| `hba1c` | `any` | No | HbA1c level |
| `hypertension` | `any` | No | 0: No, 1: Yes |
| `heart_disease` | `any` | No | 0: No, 1: Yes |
| `cp` | `any` | No | Chest pain type (0-3) |
| `trestbps` | `any` | No | Resting blood pressure |
| `chol` | `any` | No | Serum cholesterol in mg/dl |
| `fbs` | `any` | No | Fasting blood sugar > 120 mg/dl (1/0) |
| `restecg` | `any` | No | Resting ECG results (0-2) |
| `thalach` | `any` | No | Maximum heart rate achieved |
| `exang` | `any` | No | Exercise induced angina (1/0) |
| `oldpeak` | `any` | No | ST depression induced by exercise |
| `slope` | `any` | No | Slope of peak exercise ST segment |
| `ca` | `any` | No | Number of major vessels (0-4) |
| `thal` | `any` | No | Thalassemia (1-3) |
| `hdl` | `any` | No | HDL Cholesterol |
| `hyp_treatment` | `any` | No | 0: Untreated, 1: Treated |
| `total_bilirubin` | `any` | No | Total Bilirubin |
| `direct_bilirubin` | `any` | No | Direct Bilirubin |
| `alkaline_phosphotase` | `any` | No | Alkaline Phosphotase |
| `alamine_aminotransferase` | `any` | No | Alamine Aminotransferase |
| `aspartate_aminotransferase` | `any` | No | Aspartate Aminotransferase |
| `total_proteins` | `any` | No | Total Proteins |
| `albumin` | `any` | No | Albumin |
| `albumin_and_globulin_ratio` | `any` | No | Albumin And Globulin Ratio |
| `platelets` | `any` | No | Platelets in 10^9/L (Default: 250.0) |
| `bp` | `any` | No | Bp |
| `sg` | `any` | No | Sg |
| `al` | `any` | No | Al |
| `su` | `any` | No | Su |
| `rbc` | `any` | No | Rbc |
| `pc` | `any` | No | Pc |
| `pcc` | `any` | No | Pcc |
| `ba` | `any` | No | Ba |
| `bgr` | `any` | No | Bgr |
| `bu` | `any` | No | Bu |
| `sc` | `any` | No | Sc |
| `sod` | `any` | No | Sod |
| `pot` | `any` | No | Pot |
| `hemo` | `any` | No | Hemo |
| `pcv` | `any` | No | Pcv |
| `wc` | `any` | No | Wc |
| `rc` | `any` | No | Rc |
| `htn` | `any` | No | Htn |
| `dm` | `any` | No | Dm |
| `cad` | `any` | No | Cad |
| `appet` | `any` | No | Appet |
| `pe` | `any` | No | Pe |
| `ane` | `any` | No | Ane |
| `yellow_fingers` | `any` | No | Yellow Fingers |
| `anxiety` | `any` | No | Anxiety |
| `peer_pressure` | `any` | No | Peer Pressure |
| `chronic_disease` | `any` | No | Chronic Disease |
| `fatigue` | `any` | No | Fatigue |
| `allergy` | `any` | No | Allergy |
| `wheezing` | `any` | No | Wheezing |
| `coughing` | `any` | No | Coughing |
| `shortness_of_breath` | `any` | No | Shortness Of Breath |
| `swallowing_difficulty` | `any` | No | Swallowing Difficulty |
| `chest_pain` | `any` | No | Chest Pain |

### 7.NursingTaskComplete (`NursingTaskComplete`)
| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `completion_note` | `any` | No | Completion Note |

### 7.NursingTaskCreate (`NursingTaskCreate`)
| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `patient_id` | `integer` | Yes | Patient Id |
| `assigned_nurse_id` | `any` | No | Assigned Nurse Id |
| `encounter_id` | `any` | No | Encounter Id |
| `admission_id` | `any` | No | Admission Id |
| `department_id` | `any` | No | Department Id |
| `task_type` | `string` | Yes | Task Type |
| `title` | `string` | Yes | Title |
| `instructions` | `any` | No | Instructions |
| `priority` | `any` | No | Priority |
| `due_at` | `any` | No | Due At |

### 7.NursingTaskResponse (`NursingTaskResponse`)
| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `id` | `integer` | Yes | Id |
| `facility_id` | `any` | No | Facility Id |
| `patient_id` | `integer` | Yes | Patient Id |
| `assigned_nurse_id` | `any` | No | Assigned Nurse Id |
| `created_by_id` | `any` | No | Created By Id |
| `completed_by_id` | `any` | No | Completed By Id |
| `encounter_id` | `any` | No | Encounter Id |
| `admission_id` | `any` | No | Admission Id |
| `department_id` | `any` | No | Department Id |
| `task_type` | `string` | Yes | Task Type |
| `title` | `string` | Yes | Title |
| `instructions` | `any` | No | Instructions |
| `priority` | `string` | Yes | Priority |
| `status` | `string` | Yes | Status |
| `due_at` | `any` | No | Due At |
| `completed_at` | `any` | No | Completed At |
| `completion_note` | `any` | No | Completion Note |
| `created_at` | `string` | Yes | Created At |

### 7.OrderRequest (`OrderRequest`)
| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `plan_id` | `string` | No | Plan Id |

### 7.OrganSystemTrajectory (`OrganSystemTrajectory`)
> Longitudinal 10-year trajectory simulation for a specific organ system.
| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `organ` | `string` | Yes | Target organ system: cardiovascular, renal, metabolic, hepatic, neuro |
| `baseline_health_score` | `number` | Yes | Baseline organ function index (0-100) |
| `projected_score_without_intervention` | `List[number]` | Yes | Annual projected health score without intervention (Years 1-10) |
| `projected_score_with_intervention` | `List[number]` | Yes | Annual projected health score with targeted intervention (Years 1-10) |
| `relative_risk_reduction` | `number` | Yes | Calculated percentage risk reduction at year 10 |
| `key_drivers` | `List[string]` | No | Primary physiological and biomarker drivers |

### 7.PatientContext (`PatientContext`)
> Real-time patient demographic, clinical, and physiological context.
| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `patient_id` | `string` | Yes | Unique Patient Identifier (MRN or UUID) |
| `age` | `number` | Yes | Patient age in years |
| `gender` | `string` | No | Patient gender (male, female, other) |
| `bmi` | `any` | No | Body Mass Index |
| `systolic_bp` | `any` | No | Systolic Blood Pressure (mmHg) |
| `diastolic_bp` | `any` | No | Diastolic Blood Pressure (mmHg) |
| `fasting_glucose` | `any` | No | Fasting Blood Glucose (mg/dL) |
| `hba1c` | `any` | No | HbA1c percentage |
| `primary_conditions` | `List[string]` | No | Active ICD-10 or clinical diagnoses |
| `allergies` | `List[string]` | No | Known patient allergies and intolerances |
| `current_medications` | `List[string]` | No | Active medication names or RxNorm codes |
| `recent_interactions` | `List[string]` | No | Recent user interactions or clicked topics |

### 7.PatientInsightResponse (`PatientInsightResponse`)
> Serialised patient insight.
| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `id` | `integer` | Yes | Id |
| `patient_id` | `integer` | Yes | Patient Id |
| `insight_type` | `string` | Yes | Insight Type |
| `content` | `string` | Yes | Content |
| `model_version` | `any` | No | Model Version |
| `disclaimer` | `any` | No | Disclaimer |
| `created_at` | `string` | Yes | Created At |

### 7.PatientTimelineResponse (`PatientTimelineResponse`)
| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `encounters` | `List[EncounterResponse]` | Yes | Encounters |
| `admissions` | `List[AdmissionResponse]` | Yes | Admissions |
| `orders` | `List[ClinicalOrderResponse]` | Yes | Orders |
| `events` | `List[CareEventResponse]` | Yes | Events |

### 7.PharmacogenomicEvaluationRequest (`PharmacogenomicEvaluationRequest`)
> Request to evaluate drug metabolism and gene-drug interactions.
| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `patient_id` | `string` | Yes | Patient Id |
| `proposed_medications` | `List[string]` | Yes | Proposed Medications |
| `genomic_profile` | `PharmacogenomicProfile` | Yes |  |

### 7.PharmacogenomicEvaluationResponse (`PharmacogenomicEvaluationResponse`)
> Comprehensive pharmacogenomic precision prescribing analysis.
| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `patient_id` | `string` | Yes | Patient Id |
| `total_drugs_analyzed` | `integer` | Yes | Total Drugs Analyzed |
| `evaluations` | `List[DrugMetabolismReport]` | Yes | Evaluations |
| `has_critical_contraindications` | `boolean` | Yes | Has Critical Contraindications |

### 7.PharmacogenomicProfile (`PharmacogenomicProfile`)
> Patient pharmacogenomic gene variant profile.
| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `patient_id` | `string` | Yes | Patient Id |
| `cyp2d6_phenotype` | `string` | No | CYP2D6 metabolic phenotype |
| `cyp2c19_phenotype` | `string` | No | CYP2C19 metabolic phenotype |
| `slco1b1_genotype` | `string` | No | SLCO1B1 statin transport genotype |
| `vkorc1_genotype` | `string` | No | VKORC1 sensitivity |
| `hla_b5701_status` | `string` | No | HLA-B*5701 abacavir hypersensitivity |

### 7.PlanExecuteRequest (`PlanExecuteRequest`)
| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `goal` | `string` | Yes | Goal |
| `steps` | `List[object]` | Yes | Steps |

### 7.PredictionReviewCreate (`PredictionReviewCreate`)
| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `patient_id` | `integer` | Yes | Patient Id |
| `prediction_type` | `string` | Yes | Prediction Type |
| `decision` | `string` | Yes | Decision |
| `clinical_use_category` | `any` | No | Clinical Use Category |
| `model_card_id` | `any` | No | Model Card Id |
| `prediction_reference_id` | `any` | No | Prediction Reference Id |
| `review_note` | `any` | No | Review Note |

### 7.PrescriptionCreate (`PrescriptionCreate`)
| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `encounter_id` | `any` | No | Encounter Id |
| `patient_id` | `integer` | Yes | Patient Id |
| `doctor_id` | `any` | No | Doctor Id |
| `diagnosis_context` | `any` | No | Diagnosis Context |
| `items` | `List[PrescriptionItemCreate]` | Yes | Items |

### 7.PrescriptionItemCreate (`PrescriptionItemCreate`)
| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `inventory_id` | `any` | No | Inventory Id |
| `medication_name` | `string` | Yes | Medication Name |
| `dosage` | `string` | Yes | Dosage |
| `frequency` | `string` | Yes | Frequency |
| `duration` | `string` | Yes | Duration |
| `quantity_prescribed` | `number` | No | Quantity Prescribed |
| `instructions` | `any` | No | Instructions |

### 7.PrescriptionItemResponse (`PrescriptionItemResponse`)
| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `id` | `integer` | Yes | Id |
| `prescription_id` | `integer` | Yes | Prescription Id |
| `inventory_id` | `any` | No | Inventory Id |
| `medication_name` | `string` | Yes | Medication Name |
| `dosage` | `string` | Yes | Dosage |
| `frequency` | `string` | Yes | Frequency |
| `duration` | `string` | Yes | Duration |
| `quantity_prescribed` | `number` | Yes | Quantity Prescribed |
| `quantity_dispensed` | `number` | Yes | Quantity Dispensed |
| `instructions` | `any` | No | Instructions |
| `status` | `string` | Yes | Status |

### 7.PrescriptionResponse (`PrescriptionResponse`)
| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `id` | `integer` | Yes | Id |
| `facility_id` | `any` | No | Facility Id |
| `encounter_id` | `any` | No | Encounter Id |
| `patient_id` | `integer` | Yes | Patient Id |
| `doctor_id` | `any` | No | Doctor Id |
| `diagnosis_context` | `any` | No | Diagnosis Context |
| `status` | `string` | Yes | Status |
| `created_at` | `string` | Yes | Created At |
| `dispensed_at` | `any` | No | Dispensed At |
| `items` | `List[PrescriptionItemResponse]` | No | Items |

### 7.PullModelRequest (`PullModelRequest`)
| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `name` | `string` | Yes | Name |

### 7.QualityAuditRequest (`QualityAuditRequest`)
| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `records` | `List[object]` | Yes | Records |

### 7.RankedRecommendation (`RankedRecommendation`)
> Fully scored, diversified, and safety-verified recommendation.
| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `rank` | `integer` | Yes | Rank |
| `item_id` | `string` | Yes | Item Id |
| `title` | `string` | Yes | Title |
| `category` | `string` | Yes | Category |
| `description` | `string` | Yes | Description |
| `evidence_level` | `string` | Yes | Evidence Level |
| `predicted_efficacy` | `number` | Yes | Predicted clinical efficacy score |
| `safety_score` | `number` | Yes | Predicted safety score (1.0 - adverse probability) |
| `adherence_likelihood` | `number` | Yes | Predicted patient compliance likelihood |
| `composite_score` | `number` | Yes | Multi-objective calibrated rank score |
| `diversity_score` | `number` | Yes | Maximal Marginal Relevance penalty applied |
| `is_explored` | `boolean` | No | Whether selected via Thompson Sampling exploration |
| `rationale` | `string` | No | Clinical AI justification for the recommendation |

### 7.RawPatientPayload (`RawPatientPayload`)
| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `patient_id` | `string` | Yes | Patient Id |
| `year_of_birth` | `integer` | No | Year Of Birth |
| `gender` | `string` | No | Gender |
| `conditions` | `List[string]` | No | Conditions |
| `medications` | `List[string]` | No | Medications |
| `vitals` | `object` | No | Vitals |

### 7.RecommendationRequest (`RecommendationRequest`)
> Incoming request to the 4-stage recommendation engine.
| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `patient_context` | `PatientContext` | Yes |  |
| `domain` | `string` | No | Domain: clinical_intervention, lifestyle_pathway, clinical_trial |
| `top_k` | `integer` | No | Number of final recommendations to return |
| `diversity_lambda` | `number` | No | MMR trade-off factor (1.0 = pure relevance, 0.0 = max diversity) |
| `enable_exploration` | `boolean` | No | Enable Contextual Bandit exploration via Thompson Sampling |

### 7.RecommendationResponse (`RecommendationResponse`)
> Final output response from the 4-stage recommendation engine.
| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `patient_id` | `string` | Yes | Patient Id |
| `domain` | `string` | Yes | Domain |
| `total_candidates_retrieved` | `integer` | Yes | Total Candidates Retrieved |
| `total_ranked_candidates` | `integer` | Yes | Total Ranked Candidates |
| `latency_ms` | `number` | Yes | Latency Ms |
| `recommendations` | `List[RankedRecommendation]` | Yes | Recommendations |
| `medical_disclaimer` | `string` | No | Medical Disclaimer |

### 7.RecordCreate (`RecordCreate`)
| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `record_type` | `string` | Yes | Record Type |
| `data` | `object` | Yes | Data |
| `prediction` | `string` | Yes | Prediction |

### 7.ResetPasswordRequest (`ResetPasswordRequest`)
> Schema for resetting password with token
| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `token` | `string` | Yes | Token |
| `new_password` | `string` | Yes | Must meet complexity requirements |

### 7.RestoreTableRequest (`RestoreTableRequest`)
| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `table_name` | `string` | No | Table Name |
| `target_version` | `integer` | No | Target Version |

### 7.SQLExecuteRequest (`SQLExecuteRequest`)
| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `sql` | `string` | Yes | Sql |
| `warehouse_id` | `any` | No | Warehouse Id |

### 7.ScribeCommitItem (`ScribeCommitItem`)
| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `medication_name` | `string` | Yes | Medication Name |
| `dosage` | `string` | Yes | Dosage |
| `frequency` | `string` | Yes | Frequency |
| `duration` | `string` | Yes | Duration |
| `quantity_prescribed` | `number` | Yes | Quantity Prescribed |

### 7.ScribeCommitRequest (`ScribeCommitRequest`)
| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `patient_id` | `integer` | Yes | Patient Id |
| `subjective` | `string` | Yes | Subjective |
| `objective` | `string` | Yes | Objective |
| `assessment` | `string` | Yes | Assessment |
| `plan` | `string` | Yes | Plan |
| `icd10_codes` | `List[string]` | Yes | Icd10 Codes |
| `billing_codes` | `List[string]` | Yes | Billing Codes |
| `prescriptions` | `List[ScribeCommitItem]` | Yes | Prescriptions |
| `billing_items` | `List[object]` | Yes | Billing Items |

### 7.ScribeRequest (`ScribeRequest`)
| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `transcript` | `string` | Yes | Transcript |

### 7.SmartAppCreate (`SmartAppCreate`)
> Payload to register a new SMART on FHIR application.
| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `app_name` | `string` | Yes | App Name |
| `redirect_uri` | `string` | Yes | Redirect Uri |
| `launch_url` | `string` | Yes | Launch Url |
| `scopes` | `string` | No | Scopes |

### 7.SmartAppResponse (`SmartAppResponse`)
> Serialised SMART app returned to clients.
| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `id` | `integer` | Yes | Id |
| `app_name` | `string` | Yes | App Name |
| `client_id` | `string` | Yes | Client Id |
| `redirect_uri` | `string` | Yes | Redirect Uri |
| `launch_url` | `string` | Yes | Launch Url |
| `scopes` | `string` | Yes | Scopes |
| `is_active` | `boolean` | Yes | Is Active |
| `created_at` | `string` | Yes | Created At |

### 7.SmartLaunchRequest (`SmartLaunchRequest`)
> Request to create a patient-scoped launch context.
| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `app_id` | `integer` | Yes | App Id |
| `patient_id` | `integer` | Yes | Patient Id |

### 7.SmartLaunchResponse (`SmartLaunchResponse`)
> Short-lived launch context returned after a SMART launch.
| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `launch_token` | `string` | Yes | Launch Token |
| `auth_code` | `string` | Yes | Auth Code |
| `scope` | `string` | Yes | Scope |
| `expires_at` | `string` | Yes | Expires At |

### 7.SpecialCareBookingRequest (`SpecialCareBookingRequest`)
| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `patient_id` | `integer` | Yes | Patient Id |
| `doctor_id` | `any` | No | Doctor Id |
| `specialist` | `string` | Yes | Specialist |
| `date_time` | `string` | Yes | Date Time |
| `reason` | `string` | Yes | Reason |
| `request_female_clinician` | `boolean` | No | Request Female Clinician |
| `home_visit_van` | `boolean` | No | Home Visit Van |

### 7.SpecialistOpinion (`SpecialistOpinion`)
> Individual clinical deliberation from an autonomous specialist agent.
| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `specialist_role` | `string` | Yes | Role: Cardiologist, Endocrinologist, Nephrologist, Pharmacist, Patient Safety Officer |
| `diagnostic_assessment` | `string` | Yes | Diagnostic Assessment |
| `recommended_actions` | `List[string]` | Yes | Recommended Actions |
| `confidence_score` | `number` | Yes | Confidence Score |
| `contraindication_flags` | `List[string]` | No | Contraindication Flags |

### 7.StreamChatMessage (`StreamChatMessage`)
| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `role` | `string` | Yes | Role |
| `content` | `string` | Yes | Content |

### 7.StreamChatRequest (`StreamChatRequest`)
| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `message` | `string` | Yes | Message |
| `history` | `List[StreamChatMessage]` | No | History |
| `model` | `any` | No | Model |
| `rag_scope` | `any` | No | Rag Scope |
| `language` | `any` | No | Language |

### 7.StrokeInput (`StrokeInput`)
> Schema for Stroke Risk Prediction (Cerebrovascular risk)
| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `gender` | `any` | No | 0: Female, 1: Male |
| `age` | `any` | No | Age in years |
| `hypertension` | `any` | No | 0: No, 1: Yes |
| `heart_disease` | `any` | No | 0: No, 1: Yes |
| `smoking` | `any` | No | 0: No, 1: Yes |
| `bmi` | `any` | No | Body Mass Index |
| `glucose` | `any` | No | Average blood glucose level |

### 7.TOTPSetupResponse (`TOTPSetupResponse`)
| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `secret` | `string` | Yes | Secret |
| `provisioning_uri` | `string` | Yes | Provisioning Uri |
| `qr_code_base64` | `string` | Yes | Qr Code Base64 |

### 7.TOTPVerifyRequest (`TOTPVerifyRequest`)
| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `totp_code` | `string` | Yes | Totp Code |

### 7.TTSRequest (`TTSRequest`)
| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `text` | `string` | Yes | Text |
| `lang` | `string` | No | Lang |

### 7.TerminologySearchRequest (`TerminologySearchRequest`)
| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `query` | `string` | Yes | Query |

### 7.TimeTravelRequest (`TimeTravelRequest`)
| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `table_name` | `string` | No | Table Name |
| `target_version` | `integer` | No | Target Version |

### 7.Token (`Token`)
| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `access_token` | `string` | Yes | Access Token |
| `token_type` | `string` | Yes | Token Type |

### 7.TranslationRequest (`TranslationRequest`)
| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `text` | `string` | Yes | Text |
| `source_lang` | `string` | No | Source ISO language code |
| `target_lang` | `string` | No | Target ISO language code |

### 7.UserCreate (`UserCreate`)
> Schema for User Registration
| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `username` | `string` | Yes | Username |
| `password` | `string` | Yes | Must meet complexity requirements |
| `email` | `string` | Yes | Email |
| `full_name` | `string` | Yes | Full Name |
| `dob` | `string` | Yes | YYYY-MM-DD format |

### 7.UserFullResponse (`UserFullResponse`)
> Admin View: Includes sensitive health records and chat logs
| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `id` | `integer` | Yes | Id |
| `username` | `string` | Yes | Username |
| `role` | `any` | No | Role |
| `full_name` | `any` | No | Full Name |
| `email` | `any` | No | Email |
| `is_totp_enabled` | `any` | No | Is Totp Enabled |
| `health_records` | `List[HealthRecordResponse]` | No | Health Records |
| `chat_logs` | `List[ChatLogResponse]` | No | Chat Logs |

### 7.UserProfileUpdate (`UserProfileUpdate`)
> Schema for Updating User Details
| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `email` | `any` | No | Email |
| `full_name` | `any` | No | Full Name |
| `gender` | `any` | No | Gender |
| `dob` | `any` | No | Dob |
| `height` | `any` | No | Height |
| `weight` | `any` | No | Weight |
| `blood_type` | `any` | No | Blood Type |
| `existing_ailments` | `any` | No | Existing Ailments |
| `profile_picture` | `any` | No | Profile Picture |
| `about_me` | `any` | No | About Me |
| `diet` | `any` | No | Diet |
| `activity_level` | `any` | No | Activity Level |
| `sleep_hours` | `any` | No | Sleep Hours |
| `stress_level` | `any` | No | Stress Level |
| `specialization` | `any` | No | Specialization |
| `allow_data_collection` | `any` | No | Allow Data Collection |

### 7.UserResponse (`UserResponse`)
> Schema for Public User Profile
| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `id` | `integer` | Yes | Id |
| `username` | `string` | Yes | Username |
| `role` | `any` | No | Role |
| `full_name` | `any` | No | Full Name |
| `email` | `any` | No | Email |
| `is_totp_enabled` | `any` | No | Is Totp Enabled |

### 7.ValidationError (`ValidationError`)
| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `loc` | `List[any]` | Yes | Location |
| `msg` | `string` | Yes | Message |
| `type` | `string` | Yes | Error Type |
| `input` | `any` | No | Input |
| `ctx` | `object` | No | Context |

### 7.VariantShredRequest (`VariantShredRequest`)
| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `raw_json` | `string` | Yes | Raw Json |
| `target_fields` | `List[string]` | No | Target Fields |

### 7.VerifyRequest (`VerifyRequest`)
| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `gateway` | `string` | Yes | Gateway |
| `payment_intent_id` | `any` | No | Payment Intent Id |
| `razorpay_order_id` | `any` | No | Razorpay Order Id |
| `razorpay_payment_id` | `any` | No | Razorpay Payment Id |
| `razorpay_signature` | `any` | No | Razorpay Signature |
| `plan_id` | `any` | No | Plan Id |

### 7.VisitAttention (`VisitAttention`)
> Attention weight for a single visit in the sequence.
| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `visit_index` | `integer` | Yes | 0-indexed position in the visit sequence |
| `weight` | `number` | Yes | Attention weight (0-1), higher = more influential |

### 7.VitalObservationCreate (`VitalObservationCreate`)
| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `patient_id` | `integer` | Yes | Patient Id |
| `encounter_id` | `any` | No | Encounter Id |
| `department_id` | `any` | No | Department Id |
| `source` | `any` | No | Source |
| `heart_rate` | `any` | No | Heart Rate |
| `systolic_bp` | `any` | No | Systolic Bp |
| `diastolic_bp` | `any` | No | Diastolic Bp |
| `spo2` | `any` | No | Spo2 |
| `temperature_c` | `any` | No | Temperature C |
| `respiratory_rate` | `any` | No | Respiratory Rate |
| `blood_glucose` | `any` | No | Blood Glucose |
| `observed_at` | `any` | No | Observed At |

### 7.VitalObservationResponse (`VitalObservationResponse`)
| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `id` | `integer` | Yes | Id |
| `facility_id` | `any` | No | Facility Id |
| `patient_id` | `integer` | Yes | Patient Id |
| `recorded_by_id` | `any` | No | Recorded By Id |
| `encounter_id` | `any` | No | Encounter Id |
| `department_id` | `any` | No | Department Id |
| `source` | `string` | Yes | Source |
| `heart_rate` | `any` | No | Heart Rate |
| `systolic_bp` | `any` | No | Systolic Bp |
| `diastolic_bp` | `any` | No | Diastolic Bp |
| `spo2` | `any` | No | Spo2 |
| `temperature_c` | `any` | No | Temperature C |
| `respiratory_rate` | `any` | No | Respiratory Rate |
| `blood_glucose` | `any` | No | Blood Glucose |
| `observed_at` | `string` | Yes | Observed At |
| `created_at` | `string` | Yes | Created At |

### 7.VitalSubmissionResponse (`VitalSubmissionResponse`)
| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `vital` | `VitalObservationResponse` | Yes |  |
| `signals` | `List[MonitoringSignalResponse]` | Yes | Signals |

### 7.backend__explanation__ExplanationRequest (`backend__explanation__ExplanationRequest`)
| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `prediction_type` | `string` | Yes | Prediction Type |
| `input_data` | `object` | Yes | Input Data |
| `prediction_result` | `string` | Yes | Prediction Result |

### 7.backend__prediction__ExplanationRequest (`backend__prediction__ExplanationRequest`)
| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `prediction` | `string` | Yes | Prediction |
| `confidence` | `number` | Yes | Confidence |
| `risk_level` | `string` | Yes | Risk Level |
| `attributions` | `object` | Yes | Attributions |
