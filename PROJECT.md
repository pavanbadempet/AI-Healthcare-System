# Project: AI Healthcare System — AI Healthcare System Production Optimization

## Architecture

This project fully optimizes the AI Healthcare System for production based on the AI Healthcare System stack:
1. **Pure Rust Live Production Execution Stack**: Axum 0.8, Tokio, mimalloc, SQLx, and ORT ONNX with zero-allocation hot paths for all live execution, completely decoupled from Python runtime processes.
2. **Bun + React Frontend Architecture**: Bun runtime, Vite 8, local-first TanStack Query architecture with IndexedDB persistence, multi-tab sync, and optimistic UI updates connecting directly to the Rust backend services.
3. **Python Specification & Contract Synchronization**: Python code serves strictly for readability, maintainability, and contract/schema synchronization, never invoked during live production execution.

```
[ Frontend: Bun + React 19 / Vite 8 ]
   │  * Local-First TanStack Query & IndexedDB Cache
   │  * Optimistic UI Mutations (Appointments, Patients, Orders, Vitals)
   │  * Direct connection to Rust Backend on port 8000
   ▼
[ Pure Rust Live Production Backend: Axum 0.8 + Tokio ]
   │  * Global mimalloc high-throughput memory allocator
   │  * 24 native route modules (including /v1/lakehouse)
   │  * Complete severance of Python fallback proxy
   │  * AVX2 SIMD vector store & Pan-Tompkins ECG DSP (<7µs latency)
   │  * Native ORT ONNX multi-model inference & scalers
   │  * Typed SQLx connection pools (46 tables & models)
   │  * Static SPA serving for frontend/dist
   ▼
[ Database & Storage Layer ]
   │  * SQLite WAL (MMAP, 64MB memory cache) & PostgreSQL parity
   │  * Authenticated AES-256-GCM PII encryption
   │  * 46 relational models with complete index coverage
   ▼
[ Python Specification & Living Contract Layer ]
   │  * backend/ models, schemas, and routes strictly for readability & sync
   │  * 100% schema parity with Rust Serde DTOs
   │  * Production runtime lockout: raises RuntimeError if ENV=production
   │  * Automated CI verification ensuring zero live production invocations
```

---

## Feature Inventory

Every feature identified across Requirements R1, R2, and R3 during the 3-way survey:

| # | Feature / Remediation Item | Description | Milestone | Source |
|---|-----------------------------|-------------|-----------|--------|
| 1 | Global mimalloc in `main.rs` | Set `#[global_allocator] static GLOBAL: mimalloc::MiMalloc` in `rust_gateway/src/main.rs` | M1 | R1 / Rust Survey |
| 2 | PyO3 Optional Feature-Gating | Feature-gate `pyo3` as optional `python-ffi` in `rust_gateway/Cargo.toml` so pure Rust builds cleanly | M1 | R1 / Rust Survey |
| 3 | Sever Fallback Proxy to Python | Replace `proxy_handler_fallback` in `routes/mod.rs` & `main.rs` with native Axum 404 handler | M1 | R1 / Rust Survey |
| 4 | Native `/v1/lakehouse` Router | Implement `rust_gateway/src/routes/lakehouse.rs` for OMOP, quality audit, and Delta commit log history | M1 | R1 / Rust Survey |
| 5 | Port 8000 & SPA Static Serving | Bind default port to 8000 in `src/main.rs` and mount static file serving for `frontend/dist` | M1 | R1 / Rust Survey |
| 6 | Native Rust Build & Test Verification | Verify `cargo check` and `cargo test --lib --bins --tests` pass 100% with zero Python dependency | M1 | R1 / Rust Survey |
| 7 | Schema & DTO Reconciliation | Align 10 DTO divergences across `HeartInput`, `DiabetesInput`, `KidneyInput`, `PredictionReviewCreate`, etc. | M2 | R3 / Python Survey |
| 8 | Python Production Lockout | Enforce runtime check in `backend/main.py` raising `RuntimeError` if `ENV=production` | M2 | R3 / Python Survey |
| 9 | Decouple Deployment Manifests | Update `Dockerfile.enterprise`, `render.yaml`, `run_servers.py`, `run_prod.bat` to run pure Rust binary | M2 | R3 / Python Survey |
| 10 | Automated Decoupling Verification | Add automated test/script (`tests/unit/test_production_decoupling.py`) verifying Python exclusion in prod | M2 | R3 / Python Survey |
| 11 | Frontend Port & Proxy Alignment | Configure `frontend/vite.config.ts` dev server proxy and `apiCore.ts` to target Rust on port 8000 | M3 | R2 / Frontend Survey |
| 12 | Local-First IndexedDB Persistence | Configure `QueryClient` with IndexedDB persistence, `networkMode: 'offlineFirst'`, and multi-tab sync | M3 | R2 / Frontend Survey |
| 13 | Modular TanStack Query Hooks | Implement `useAppointments`, `usePatients`, `usePatientDetail`, `useHospitalCapacity`, `useClinicalIntelligence` | M3 | R2 / Frontend Survey |
| 14 | Optimistic UI Mutations | Implement 3-phase optimistic UI (`onMutate` -> `onError` -> `onSettled`) in core clinical views | M3 | R2 / Frontend Survey |
| 15 | Frontend Build & Vitest Verification | Verify `bun run build` and `bun run test` (104/104 tests) pass with QueryClient providers | M3 | R2 / Frontend Survey |
| 16 | Dual-Track Full Regression Verification | Execute complete Rust, Frontend (Bun), and Python test suites with zero regressions | M4 | E2E Track / AC |
| 17 | Forensic Integrity Audit | Independent verification of authentic implementation, zero dummy facades, and clean audit verdict | M4 | Forensic Audit / AC |

---

## Milestones

| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| M1 | Pure Rust Live Production Execution Stack | Add mimalloc in main.rs, feature-gate PyO3, sever proxy fallback, add /v1/lakehouse router, bind port 8000, verify cargo tests | none | DONE |
| M2 | Python Specification & Contract Synchronization | Reconcile 10 DTO discrepancies, add production runtime lockout in backend/main.py, decouple deployment manifests, add decoupling test | none | DONE |
| M3 | Bun + React Local-First TanStack Query Architecture | Configure Vite proxy to port 8000, set up QueryClient with IndexedDB persister, build modular query hooks, implement optimistic UI | M1 | DONE |
| M4 | Full Regression Verification & Forensic Integrity Audit | Run full Rust test suite, Bun frontend test suite, Python contract test suite, decoupling verification, and Forensic Audit | M1, M2, M3 | DONE |

---

## Interface Contracts

### 1. Pure Rust Gateway API (`rust_gateway/`)
- Default listening port: `8000` (configurable via `PORT` or `RUST_PORT`).
- Unmatched endpoints return structured JSON 404: `{"error": "Not Found", "message": "Endpoint not recognized"}`. No request is forwarded to Python.
- `/v1/lakehouse` route contracts:
  - `POST /v1/lakehouse/omop/transform`: accepts table transformation payload, returns standard OMOP conversion status.
  - `POST /v1/lakehouse/quality/audit`: accepts audit parameters, returns Great Expectations quality metrics summary.
  - `GET /v1/lakehouse/delta/history`: returns Delta Lake versioned commit logs.

### 2. Python Contract Mirror (`backend/`)
- `backend/schemas/prediction.py`:
  - `HeartInput`: exactly mirrors `rust_gateway/src/ml/predictors.rs:HeartInput` with 13 required float fields (`age`, `sex`, `cp`, `trestbps`, `chol`, `fbs`, `restecg`, `thalach`, `exang`, `oldpeak`, `slope`, `ca`, `thal`) and optional clinical indicators with defaults.
  - `DiabetesInput`: exactly mirrors `rust_gateway/src/ml/predictors.rs:DiabetesInput`.
  - `KidneyInput`: `is_female: Optional[bool]` aligned with Rust.
  - `PredictionReviewCreate`: `clinician_agree: bool`, `model_prediction: str`, `revised_diagnosis: Optional[str]`, `notes: Optional[str]`.
- `backend/main.py`:
  - Startup hook evaluates `os.getenv("ENV") == "production" or os.getenv("ENVIRONMENT") == "production"`.
  - If true, raises `RuntimeError("Python execution is disabled in live production mode. All requests must be handled by the native Rust Gateway.")`.

### 3. Frontend TanStack Query Architecture (`frontend/`)
- API Base URL: `http://127.0.0.1:8000/v1` (or Vite proxy `/v1`).
- Query keys follow hierarchical array convention:
  - `['appointments', 'list', filters]`
  - `['patients', 'list', page, search]`
  - `['patient', patientId, 'detail']`
  - `['patient', patientId, 'vitals']`
  - `['hospital', 'capacity']`
  - `['clinical-intelligence', 'alerts']`
- Optimistic mutations implement:
  - `onMutate`: cancel outgoing refetches, snapshot previous cache, optimistically set new data with temporary ID.
  - `onError`: rollback cache to previous snapshot, show toast error.
  - `onSettled`: invalidate query key to trigger background reconciliation.

---

## Code Layout

```
AI-Healthcare-System/
├── rust_gateway/                        # Pure Rust Live Production Backend (Axum 0.8, Tokio, mimalloc)
│   ├── Cargo.toml                       # Dependencies (Axum, Tokio, SQLx, ORT, mimalloc, optional pyo3)
│   ├── src/
│   │   ├── main.rs                      # Binary entrypoint (mimalloc, port 8000, static SPA serving)
│   │   ├── lib.rs                       # Library & shared utilities
│   │   ├── auth.rs                      # Native JWT authentication & bcrypt
│   │   ├── routes/                      # 24 native domain routers (including lakehouse.rs)
│   │   ├── db/                          # SQLx schemas, migrations, and typed repositories
│   │   ├── ml/                          # ORT ONNX inference engine, scalers, and predictors
│   │   └── vector_store.rs              # AVX2 SIMD zero-allocation vector search (<7µs)
├── frontend/                            # Bun + React 19 / Vite 8 Frontend SPA
│   ├── package.json                     # Bun scripts & dependencies (@tanstack/react-query, idb-keyval)
│   ├── vite.config.ts                   # Vite 8 config with proxy to http://127.0.0.1:8000
│   └── src/
│       ├── main.tsx                     # QueryClient setup with IndexedDB persister
│       ├── hooks/                       # Modular TanStack Query & optimistic mutation hooks
│       ├── pages/                       # Modular page views with local-first responsive caching
│       └── lib/apiCore.ts               # Direct connection to Rust backend (port 8000)
├── backend/                             # Python Living Specification & Contract Layer
│   ├── main.py                          # Production lockout guard & OpenAPI specification exporter
│   ├── models/                          # SQLAlchemy database models mirroring Rust SQLx models
│   ├── schemas/                         # Pydantic V2 schemas mirroring Rust Serde DTOs
│   └── routes/                          # Specification routes for developer readability
└── tests/                               # Comprehensive Automated Test Suites
    ├── unit/test_production_decoupling.py # Automated verification that live prod decouples Python
    └── ...                              # Pytest test suite ensuring specification parity
```
