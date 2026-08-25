# Original User Request

## 2026-08-21T05:13:17Z

Rewrite the AI Healthcare System for maximum performance. The current Python/FastAPI backend (~170 files, ~40 route modules) must be replaced with a Rust (Axum/Tokio) backend for all compute-heavy work and a Bun (ElysiaJS) API orchestration layer for routing, SSR, middleware, and lightweight endpoints. Python is eliminated entirely — ML inference moves to ONNX Runtime in Rust. The existing Vite+React 19 frontend already uses Bun and is unchanged. This is a production upgrade — every existing API endpoint must continue to work with the same contracts so the frontend doesn't break.

Working directory: c:\Users\pavan\OneDrive\Documents\GitHub\AI-Healthcare-System
Integrity mode: development

The existing codebase already has a partial Rust gateway at `rust_gateway/` (Axum, Tokio, PyO3, sqlx, tonic/gRPC) with modules for auth, appointments, FHIR, telehealth, claims, vector store, telemetry, clinical calculator, DICOM, ECG DSP, PHI redaction, federated aggregation, billing audit, and TEE enclave. ONNX model files already exist at `backend/*.onnx` for diabetes, heart disease, kidney, liver, and lungs predictors (with scalers). The frontend at `frontend/` uses Bun, Vite, React 19, TailwindCSS 4, and TypeScript.

## Requirements

### R1. Rust Backend — Full API Coverage

Expand the existing `rust_gateway/` into the primary backend server. It must serve every API endpoint currently registered in `backend/main.py` (~40 router modules covering: auth, chat, streaming chat, prediction, explanation, reports, admin, sales readiness, demo readiness, hospital operations, monitoring, diagnostics, pharmacy, billing, discharge, nursing, care events, interoperability, payments, telemetry, appointments, DICOM web, Ollama routes, longitudinal prediction, SMART FHIR, FHIR endpoints, federated sync, clinical intelligence, consent gate, i18n audio, FHIR compression, ABDM sandbox, data platform, recommendation, peak healthcare, data engineering, mesh, and four-eye review). The Rust server must preserve the same REST API contracts (paths, request/response JSON shapes, status codes, auth headers) so the React frontend works without changes. Database access must use sqlx supporting both SQLite (local dev) and PostgreSQL (production), selected via `DATABASE_URL` environment variable. All SQLAlchemy models from `backend/models/` (auth, appointments, billing, clinical, discharge, hospital, nursing, pharmacy, federated, interoperability, intelligence, records, data governance, smart app) must have equivalent Rust structs and sqlx queries.

### R2. Bun ElysiaJS API Orchestration Layer

Create a Bun-powered ElysiaJS server that sits as the edge entry point (PID 1 in production). It handles: request routing and proxying to the Rust backend, response caching, rate limiting, CORS, compression, request validation, authentication middleware (JWT verification), health check aggregation, metrics collection, and static asset serving for the frontend SPA. The ElysiaJS layer provides the BFF (Backend-for-Frontend) pattern — it can aggregate multiple Rust backend calls into single frontend responses where beneficial. WebSocket connections for streaming chat and telemetry are proxied through to the Rust backend.

### R3. ONNX Runtime ML Inference in Rust

All ML prediction endpoints (diabetes, heart disease, kidney disease, liver disease, lung disease, stroke risk, longitudinal predictions) must run inference using the `ort` crate (ONNX Runtime for Rust) loading the existing `.onnx` model files. No Python dependency for inference. Scalers (kidney, liver, lungs) must be reimplemented as native Rust preprocessing using the parameters from the existing `.onnx` scaler files. The prediction API response format must remain identical to the current Python implementation.

### R4. Existing Codebase Compatibility

The rewrite is in-place within the existing repository. The frontend (`frontend/`) must not be modified except for any proxy/API base URL configuration changes needed to point at the new ElysiaJS edge layer. All existing test expectations from `tests/` describe the correct API behavior — the new implementation must satisfy them. Environment variables, Docker configurations, and deployment manifests (k8s/, terraform/, docker-compose files) should be updated to reflect the new Rust+Bun architecture.

## Acceptance Criteria

### API Parity
- [ ] Every REST endpoint currently registered in `backend/main.py` has an equivalent endpoint in the Rust backend returning the same JSON response shapes
- [ ] The frontend application loads and operates without modification against the new backend stack
- [ ] Authentication flow (JWT token issue, verify, refresh) works identically
- [ ] WebSocket endpoints for streaming chat and telemetry connect and stream data

### Performance
- [ ] The Rust backend starts in under 2 seconds (vs current Python cold start)
- [ ] API response latency for prediction endpoints is measurably lower than the Python implementation (benchmark script provided)
- [ ] The ElysiaJS edge layer adds less than 5ms overhead per proxied request

### ML Inference
- [ ] All 5 disease prediction models (diabetes, heart, kidney, liver, lungs) produce identical outputs to the Python implementation for the same inputs (within floating-point tolerance of 1e-6)
- [ ] ONNX scaler preprocessing produces identical scaled values to the Python sklearn scalers
- [ ] No Python process is required for any ML inference

### Build & Deploy
- [ ] `cargo build --release` in `rust_gateway/` produces a working binary
- [ ] `bun install && bun run` in the ElysiaJS project starts the edge server
- [ ] The full stack runs locally with SQLite using only `DATABASE_URL=sqlite:///./healthcare.db`
- [ ] Docker builds succeed for the new architecture
- [ ] Existing pytest tests in `tests/` pass against the new backend (with connection pointed at the new server)
