## 2026-08-21T05:50:00Z

### Milestone 3: Full Rust API Router & Endpoint Implementation (~40 modules, 289 paths, WebSockets, SSE)
**Working Directory**: c:\Users\pavan\OneDrive\Documents\GitHub\AI-Healthcare-System\.agents\sub_orch_m3_1
**Original Request**: c:\Users\pavan\OneDrive\Documents\GitHub\AI-Healthcare-System\.agents\ORIGINAL_REQUEST.md
**Project Spec**: c:\Users\pavan\OneDrive\Documents\GitHub\AI-Healthcare-System\PROJECT.md
**Routes Specification**: c:\Users\pavan\OneDrive\Documents\GitHub\AI-Healthcare-System\.agents\explorer_survey_routes_1\routes_survey.md
**Route Manifest**: c:\Users\pavan\OneDrive\Documents\GitHub\AI-Healthcare-System\.agents\explorer_survey_routes_1\route_manifest.json

**Objective**:
Expand `rust_gateway/src/routes/` and `rust_gateway/src/main.rs` to serve every API endpoint currently registered in `backend/main.py` (~40 router domains, 289 unique REST paths, WebSockets, SSE streams), utilizing `DbPool` and `InferenceManager` from M1 and M2, preserving exact REST API contracts, JSON shapes, auth headers, and status codes.

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
3. Mount all router modules into `AppState` and Axum router in `rust_gateway/src/main.rs` and `lib.rs`.
4. Run `cargo check` and `cargo test` in `rust_gateway/`.
5. Execute the E2E test suite against the Rust backend server to verify endpoint parity:
   `python e2e_tests/run_e2e.py`
6. Write `handoff.md` and send a message to the orchestrator when complete.

**MANDATORY INTEGRITY WARNING**:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.
