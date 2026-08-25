# Project: AI Healthcare System Full-Stack Rust + Bun Rewrite

## Architecture

The system transitions from a Python/FastAPI monolithic backend to a zero-Python, dual-tier high-performance architecture:

```
[ Frontend: React 19 + Vite SPA (Bun) ]
                 │
                 ▼ (HTTP / WebSockets on Port 3000/8000)
┌───────────────────────────────────────────────────────────┐
│ Tier 1: Bun + ElysiaJS API Orchestration Layer (BFF)      │
│  - Edge entry point & PID 1 in container                  │
│  - CORS, Compression, Request Validation                  │
│  - JWT Verification & Rate Limiting                       │
│  - WebSocket & SSE Proxying                               │
│  - Static Asset Serving & Health Aggregation              │
└────────────────────────────┬──────────────────────────────┘
                             │ (High-throughput Loopback HTTP / IPC)
                             ▼ (Port 8001)
┌───────────────────────────────────────────────────────────┐
│ Tier 2: Rust Gateway Backend Server (Axum + Tokio)        │
│  - 100% REST API parity (~40 router domains, 289 paths)   │
│  - Native ONNX Runtime (`ort`) for all ML disease models  │
│  - Native static scaler math (0.0 error vs sklearn)       │
│  - Dual `sqlx` Database Engine (SQLite WAL & PostgreSQL)  │
│  - Real-time WebSocket Telemetry & SSE Streaming          │
│  - TEE Enclave, FHIR compression, DSP & Clinical Calcs   │
└────────────────────────────┬──────────────────────────────┘
                             │
                             ▼
         [ Database: SQLite WAL / PostgreSQL ]
```

## Feature Inventory

| # | Feature | Description | Milestone | Source |
|---|---------|-------------|-----------|--------|
| 1 | Dual DB Engine (sqlx) | SQLite WAL mode & PostgreSQL connection pool with dynamic `DATABASE_URL` resolution | M1 | DB Survey |
| 2 | Complete Entity Structs | 46 database models mapped to Rust `sqlx::FromRow` structs across 15 domains | M1 | DB Survey |
| 3 | PII Encryption Compatibility | AES-GCM / PKCS7 database encryption compatible with `DB_ENCRYPTION_KEY` | M1 | DB Survey |
| 4 | Schema Migrations & Auto-init | Automatic table creation and indexing on SQLite/PostgreSQL startup | M1 | DB Survey |
| 5 | Native ONNX Engine (`ort`) | In-memory ONNX Runtime session pool for Diabetes, Heart, Kidney, Liver, Lungs, Stroke | M2 | ML Survey |
| 6 | Native Rust Scalers | Zero-allocation static float vector linear scalers $(X - \text{offset}) \times \text{scale}$ with `log1p` | M2 | ML Survey |
| 7 | Clinical Risk Calculators | Native Rust eGFR, FIB-4, Framingham, and Longitudinal Heuristic prediction pipelines | M2 | ML Survey |
| 8 | Prediction REST APIs | `/v1/predict/*`, `/v1/explain/*`, `/v1/longitudinal-predict/*` preserving exact response DTOs | M2 | Routes Survey |
| 9 | Authentication & 2FA | OAuth2 `/v1/token`, JWT HS256 issue/verify/refresh, TOTP 2FA setup/enable, Brute-force protection | M3 | Routes Survey |
| 10 | Clinical & Hospital Ops | Facilities, departments, beds, admissions, encounters, clinical orders, care events, vitals | M3 | Routes Survey |
| 11 | Billing, Invoices & Claims | Billable services, invoices, line items, payments, insurance claims, billing audit | M3 | Routes Survey |
| 12 | Pharmacy & Prescriptions | Medication inventory, prescriptions, items, dispense records, drug interactions | M3 | Routes Survey |
| 13 | Nursing & Care Tasks | Nursing task queue, priority scheduling, completion tracking | M3 | Routes Survey |
| 14 | Interoperability & FHIR | ABDM consent flow, ABHA linking, SMART on FHIR launch, FHIR resources & compression | M3 | Routes Survey |
| 15 | Intelligence & Diagnostics | Clinical alerts, patient insights, AI corrections, diagnostic lab results, DICOM slicer | M3 | Routes Survey |
| 16 | Data Platform & Governance | Data catalog, lineage, schema contracts, contract violations, feature attribution logs | M3 | Routes Survey |
| 17 | Streaming Chat & SSE | `POST /v1/chat/stream` SSE token streaming with RAG context & heartbeat keepalives | M3 | Routes Survey |
| 18 | Real-Time Telemetry WS | WebSockets `/v1/telemetry/stream` (token auth, 2s interval) & `/v1/telemetry/vitals/{id}` | M3 | Routes Survey |
| 19 | Licensing & Admin Routes | License tier enforcement, system metrics (`/metrics`), health checks (`/healthz/*`), admin management | M3 | Routes Survey |
| 20 | Bun ElysiaJS Edge Server | High-performance edge server with ElysiaJS on Bun runtime (PID 1 entry point) | M4 | Original Request |
| 21 | Edge JWT Auth & Rate Limiting | Edge-level JWT authentication guard, IP rate limiter, and CORS headers | M4 | Original Request |
| 22 | WebSocket & SSE Edge Proxy | High-speed transparent proxying for WebSockets and SSE streams to Rust backend | M4 | Original Request |
| 23 | Static SPA Serving | Serving Vite React 19 frontend assets with compression and fallback routing | M4 | Original Request |
| 24 | E2E Testing Suite (Tiers 1-4) | Opaque-box comprehensive test suite covering all 40 domains and 305 HTTP operations | E2E Track | Original Request |
| 25 | Adversarial Hardening (Tier 5) | White-box stress tests, boundary conditions, edge cases, zero-Python verification | M5 | Original Request |
| 26 | Deployment & Containerization | Dockerfiles (Rust multi-stage + Bun Elysia), docker-compose, k8s manifests update | M5 | Original Request |

## Milestones

| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| E2E | E2E Testing Suite & Infrastructure | Opaque-box test suite (Tiers 1-4) covering all 40 domains, test harness, runner, `TEST_READY.md` | none | DONE |
| M1 | Rust Database Models & sqlx Migration | All 46 database entities, dual SQLite/Postgres `DbPool`, AES-GCM PII encryption, schema init | none | DONE |
| M2 | Native Rust ONNX ML Inference Engine | `ort` runtime integration, static scalers, 6 disease models, longitudinal prediction & clinical calculators | none | DONE |
| M3 | Full Rust API Coverage & WebSockets | Axum routes covering all 40 router domains, 289 REST paths, auth workflows, WS telemetry, SSE chat | M1, M2 | DONE |
| M4 | Bun ElysiaJS API Orchestration Layer | Bun + ElysiaJS edge gateway, reverse proxy, JWT middleware, rate limiting, WS proxy, static SPA serving | M3 | DONE |
| M5 | Integration, 100% E2E Pass & Docker Deploy | Full system integration, pass 100% E2E test suite, Tier 5 adversarial hardening, update Dockerfiles/k8s | E2E, M3, M4 | DONE |

## Interface Contracts

### Bun ElysiaJS Edge Gateway ↔ Rust Backend
- **Protocol**: HTTP/1.1 & HTTP/2 over loopback (`http://127.0.0.1:8001`) with streaming WebSockets (`ws://127.0.0.1:8001`).
- **Headers**:
  - `Authorization: Bearer <jwt>` passed transparently.
  - `X-Forwarded-For`, `X-Real-IP`, `X-Request-ID` injected by ElysiaJS.
  - `X-AI-Provider`, `X-AI-API-Key` forwarded for external provider overrides.
- **WebSocket Auth**: `?token=<jwt>` query param passed directly to Rust backend `/v1/telemetry/stream`.
- **SSE Stream**: `POST /v1/chat/stream` piped directly with `Content-Type: text/event-stream` and chunked transfer encoding.

### Rust Axum Backend ↔ Database (sqlx)
- **Dynamic Pool**: `DbPool::Sqlite(SqlitePool)` when `DATABASE_URL` starts with `sqlite:`, `DbPool::Postgres(PgPool)` when `DATABASE_URL` starts with `postgres:` or `postgresql:`.
- **Transaction Safety**: Atomic transactions for billing payments, appointment booking, inventory dispensing, and auth registration.

### Rust ONNX Inference Engine ↔ REST API
- **Input DTOs**: Strict JSON deserialization matching Pydantic schemas (e.g. `DiabetesPredictionRequest`, `HeartPredictionRequest`, etc.).
- **Output DTOs**: Deterministic JSON responses matching `PredictionResponse` (`{"prediction": 1, "probability": 0.85, "risk_level": "High", "confidence": 0.92, ...}`).

## Code Layout

```
c:\Users\pavan\OneDrive\Documents\GitHub\AI-Healthcare-System/
├── rust_gateway/                     # Primary Rust Backend Server (Axum + Tokio)
│   ├── Cargo.toml                    # Dependencies: axum, tokio, sqlx, ort, aes-gcm, serde, jsonwebtoken
│   ├── src/
│   │   ├── main.rs                   # Server entry point, CLI args, DB pool init, router mounting
│   │   ├── lib.rs                    # Core library & exports
│   │   ├── db/                       # sqlx database pool & migrations
│   │   │   ├── mod.rs                # DbPool enum (Sqlite / Postgres)
│   │   │   ├── schema.rs             # Table DDL definitions for auto-init
│   │   │   ├── crypto.rs             # AES-GCM PII column encryption/decryption
│   │   │   └── repo.rs               # CRUD repositories
│   │   ├── models/                   # 46 Rust structs with sqlx::FromRow & Serde
│   │   │   ├── mod.rs
│   │   │   ├── auth.rs
│   │   │   ├── appointments.rs
│   │   │   ├── billing.rs
│   │   │   ├── clinical.rs
│   │   │   ├── hospital.rs
│   │   │   ├── pharmacy.rs
│   │   │   ├── nursing.rs
│   │   │   ├── fhir.rs
│   │   │   ├── intelligence.rs
│   │   │   └── governance.rs
│   │   ├── ml/                       # Native Rust ONNX Inference Engine
│   │   │   ├── mod.rs                # Model registry & inference session pool
│   │   │   ├── scalers.rs            # Native static const float scalers
│   │   │   ├── engine.rs             # `ort` session execution & tensor mapping
│   │   │   ├── predictors.rs         # Diabetes, Heart, Kidney, Liver, Lung, Stroke
│   │   │   └── longitudinal.rs       # Longitudinal trend & heuristic scoring
│   │   ├── routes/                   # Axum Route Handlers (~40 modules)
│   │   │   ├── mod.rs
│   │   │   ├── auth.rs
│   │   │   ├── prediction.rs
│   │   │   ├── chat.rs
│   │   │   ├── appointments.rs
│   │   │   ├── hospital.rs
│   │   │   ├── billing.rs
│   │   │   ├── pharmacy.rs
│   │   │   ├── nursing.rs
│   │   │   ├── telemetry.rs
│   │   │   ├── fhir.rs
│   │   │   ├── intelligence.rs
│   │   │   └── admin.rs
│   │   └── middleware/               # Auth guards, facility tenancy, licensing gate
├── edge_gateway/                     # Bun + ElysiaJS API Orchestration Layer (PID 1)
│   ├── package.json                  # Dependencies: elysia, @elysiajs/cors, @elysiajs/jwt, etc.
│   ├── tsconfig.json
│   ├── src/
│   │   ├── index.ts                  # Elysia server entry point
│   │   ├── proxy.ts                  # Reverse proxy to Rust backend (HTTP & WS)
│   │   ├── middleware/               # CORS, JWT, rate limiting, compression
│   │   └── static.ts                 # Static asset server for frontend SPA
├── frontend/                         # Vite + React 19 SPA (Unmodified)
├── tests/                            # Pytest / Integration test suites
└── e2e_tests/                        # Requirement-driven Opaque-box E2E Test Suite
    ├── harness/                      # Test runner & reporting
    ├── tiers/                        # Tiers 1-4 test cases
    └── run_e2e.py / run_e2e.ts       # Standalone test runner
```
