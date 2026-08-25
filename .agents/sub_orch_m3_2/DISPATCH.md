## 2026-08-21T05:55:00Z

### Milestone 3: Full Rust API Router & Endpoint Implementation (~40 modules, 289 paths, WebSockets, SSE)
**Working Directory**: c:\Users\pavan\OneDrive\Documents\GitHub\AI-Healthcare-System\.agents\sub_orch_m3_2
**Original Request**: c:\Users\pavan\OneDrive\Documents\GitHub\AI-Healthcare-System\.agents\ORIGINAL_REQUEST.md
**Project Spec**: c:\Users\pavan\OneDrive\Documents\GitHub\AI-Healthcare-System\PROJECT.md
**Routes Specification**: c:\Users\pavan\OneDrive\Documents\GitHub\AI-Healthcare-System\.agents\explorer_survey_routes_1\routes_survey.md
**Route Manifest**: c:\Users\pavan\OneDrive\Documents\GitHub\AI-Healthcare-System\.agents\explorer_survey_routes_1\route_manifest.json

**Objective**:
Implement all Axum route handlers in `rust_gateway/src/routes/` and mount them in `rust_gateway/src/main.rs`, serving all ~40 router domains and 289 REST paths + WebSockets + SSE streams with `DbPool` and `InferenceManager`, preserving REST API contracts, JSON shapes, auth headers, and status codes.

**Instructions**:
1. Read `ORIGINAL_REQUEST.md`, `PROJECT.md`, `routes_survey.md`, and `route_manifest.json`.
2. Implement Axum route modules in `rust_gateway/src/routes/`:
   - `auth.rs`: `/v1/token`, `/v1/signup`, `/v1/me`, `/v1/users`, `/v1/2fa/*`, `/v1/forgot-password`, `/v1/reset-password`.
   - `prediction.rs`: `/v1/predict/*` (diabetes, heart, kidney, liver, lungs, stroke, multi-organ), `/v1/predict/explain/*`, `/v1/predict/longitudinal/*`.
   - `chat.rs`: `/v1/chat`, `POST /v1/chat/stream` SSE stream with keepalive `:heartbeat` and RAG injection.
   - `hospital.rs`: facilities, departments, beds, admissions, encounters, clinical orders, vitals.
   - `billing.rs`: billable services, invoices, payments, insurance claims, billing audit.
   - `pharmacy.rs`: medication inventory, prescriptions, dispense records, drug interactions.
   - `appointments.rs`: scheduling, rescheduling, doctor list, specialist recommendation, `POST /v1/appointments/agent-stream` SSE.
   - `diagnostics.rs`: lab orders, result submission, DICOM slicer, ECG DSP.
   - `nursing.rs`: nursing tasks queue, task updates, handoffs.
   - `monitoring.rs`: inpatient vitals submission, clinical signals.
   - `discharge.rs`: discharge summaries, review, export.
   - `care_events.rs`: event dispatcher, patient feed, doctor feed.
   - `telemetry.rs`: WebSocket `/v1/telemetry/stream` (token auth, 2.0s interval), `/v1/telemetry/vitals/{id}`, HL7 ingestion.
   - `fhir.rs`: FHIR R4 resources, compression (`compact`/`decompress`), ABDM consent.
   - `smart.rs`: SMART on FHIR launch, well-known config, token exchange.
   - `intelligence.rs`: clinical alerts, patient insights, explainability graph.
   - `governance.rs`: four-eye AI reviews, audit ledger, contracts.
   - `data_platform.rs`: lakehouse SQL, data catalog, lineage, cost analyzer, sepsis deterioration.
   - `federated.rs`: model feedback, federated sync.
   - `licensing.rs`: license status, tier enforcement (`enforce_license_tier`).
   - `admin.rs`: system stats, user RBAC, audit logs, backup readiness, sales readiness.
   - `top_level.rs`: `GET /`, `/healthz`, `/healthz/env`, `/healthz/circuit_breaker`, `/healthz/time_predict`, `/metrics`, `/generate_report`, `/v1/demo-readiness`.
   - `mod.rs`: Combine all into `pub fn build_app_router(state: AppState) -> Router`.
3. Mount in `rust_gateway/src/main.rs` and `lib.rs`.
4. Run `cargo check` and `cargo test` in `rust_gateway/`.
5. Write `handoff.md` and notify orchestrator when complete.
