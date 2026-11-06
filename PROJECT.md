# Project: AI Healthcare System — Production Hardening & Architecture Alignment

## Architecture

This project hardens and aligns the AI Healthcare System codebase against the 5 core architecture playbooks in `docs/architecture/` and imported skills in `.agents/skills/`:
1. `docs/architecture/AI_AGENT_DATABASE_ENGINEERING_PLAYBOOK.md`
2. `docs/architecture/AI_AGENT_BACKEND_ENGINEERING_PLAYBOOK.md`
3. `docs/architecture/AI_AGENT_DATA_ENGINEERING_PLAYBOOK.md`
4. `docs/architecture/AI_AGENT_FRONTEND_ENGINEERING_PLAYBOOK.md`
5. `docs/architecture/MASTER_PERFORMANCE_ARCHITECTURE_PLAN.md`

```
[ Frontend: React / Vite SPA ]
   │  * Modular sub-components (<600 LOC)
   │  * TanStack Query caching & state management
   │  * Optimized bundle chunks (eliminated ineffective dynamic imports)
   ▼
[ Rust Edge Gateway (rust_gateway/) - Axum 0.8 + Tokio ]
   │  * Reverse proxy fallback to Python backend
   │  * AVX2 SIMD vector search & ONNX acceleration
   │  * Thread-safe AppState licensing (zero unsafe env::set_var)
   ▼
[ Backend: FastAPI (backend/) ]
   │  * Clean service & route modularity (<600 LOC per file)
   │  * prediction.py decomposed into engine, calculators, and routes
   │  * main.py lifespan diagnostics extracted to lifecycle.py
   │  * Centralized prompts via prompt_registry.py
   │  * Strict Pydantic V2 response models & Depends(database.get_db)
   ▼
[ Database & Data Layer ]
   │  * 31 Foreign Key indexes added (Rule DB-FK-002)
   │  * High-frequency composite indexes (chat_logs, appointments, orders)
   │  * ClinicalAICorrection re-exported in models/__init__.py
   │  * Zero-config SQLite WAL offline sandbox & PostgreSQL parity
   │  * Medallion lakehouse pipelines (<600 LOC) & sanitized credentials
```

---

## Feature Inventory

Every feature and remediation item identified during the 3-way architecture survey:

| # | Feature / Remediation Item | Description | Milestone | Source |
|---|-----------------------------|-------------|-----------|--------|
| 1 | 31 Foreign Key Indexes | Add indexes to 31 unindexed foreign key columns across 15 models (Rule `DB-FK-002`) | M1 | DB Playbook / Data Survey |
| 2 | High-Frequency Composite Indexes | Add composite indexes (`chat_logs(user_id, timestamp)`, `appointments(doctor_id, date_time)`, etc.) | M1 | DB Playbook / Performance Plan |
| 3 | Model Re-export Discovery | Export `ClinicalAICorrection` in `backend/models/__init__.py` for Alembic metadata tracking | M1 | DB Playbook / Data Survey |
| 4 | Pharmacy Concurrency Guard | Add row locking (`with_for_update()`) and `CHECK (quantity_on_hand >= 0)` constraint | M1 | DB Playbook / Data Survey |
| 5 | Decompose `backend/prediction.py` | Split 3,522 LOC monolith into modular calculators, attribution, engine, and routes (<600 LOC) | M2 | Backend Playbook / AGENTS.md |
| 6 | Decompose `backend/main.py` | Extract 800+ lines of startup diagnostics and migrations into `backend/lifecycle.py` (<600 LOC) | M2 | Backend Playbook / AGENTS.md |
| 7 | System Prompt Centralization | Move 34+ inlined prompt strings into `backend/prompt_registry.py` | M2 | Backend Playbook / AGENTS.md |
| 8 | Rust Gateway Concurrency Safety | Replace `unsafe { env::set_var }` in `licensing.rs` with thread-safe `AppState` / atomic state | M2 | Backend Playbook / Performance Plan |
| 9 | Direct `SessionLocal()` Elimination | Replace synchronous `SessionLocal()` in `core_ai.py` and `prediction.py` with async logging | M2 | Backend Playbook / AGENTS.md |
| 10 | Data Pipeline Modularity | Decompose `backend/data_engineering_platform.py` (1,225 LOC) and Airflow DAGs (<600 LOC) | M3 | Data Playbook / AGENTS.md |
| 11 | Notebook Credential Sanitization | Remove plaintext `"adminpass"` fallback in `databricks_notebooks/01_bronze_ingest.py:54` | M3 | Data Playbook / Security Audit |
| 12 | Frontend Monolith Decomposition | Modularize `Dashboard.tsx` (2,020 LOC), `ClinicalIntelligence.tsx` (1,646 LOC), etc. into subcomponents (<600 LOC) | M4 | Frontend Playbook / AGENTS.md |
| 13 | TanStack Query Integration | Implement `useQuery` / `useMutation` hooks for clinical data fetching and cache management | M4 | Frontend Playbook / Performance Plan |
| 14 | Dynamic Import & Bundle Optimization | Eliminate barrel import bottlenecks in `src/lib/api.ts` to restore clean code splitting | M4 | Frontend Playbook / Performance Plan |
| 15 | Accessibility & Test Flake Fixes | Add `aria-label` to buttons, fix duplicate key in `ComplianceCopy.test.tsx`, mock test sockets | M4 | Frontend Playbook / Quality Gate |
| 16 | Performance Budgets & Edge Profiling | Align edge proxy timeouts, memory zeroing, and sub-100ms response targets | M5 | Performance Plan |
| 17 | Backend Test Regression Fixes | Resolve isolated test assertions in scheduling agent and backup readiness staleness | M5 | Backend Audit / Quality Gate |
| 18 | Dual-Track Full Regression Verification | Run full backend (`pytest tests/ -n auto`) and frontend (`bun test`) suites with 0 failures | M6 | E2E Track / Orchestration |
| 19 | Forensic Integrity Audit | Independent verification of genuine implementations, zero facades, zero mocks in production | M6 | Orchestration / Auditor Gate |

---

## Milestones

| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| M1 | Database Architecture & Indexing Hardening | Add 31 FK indexes, composite query indexes, re-export missing models, add concurrency guards | none | DONE |
| M2 | Backend API & Service Modularity Alignment | Split `prediction.py` and `main.py` (1,148 LOC -> 458 LOC), centralize prompts, fix Rust concurrency | M1 | DONE |
| M3 | Data Engineering & Pipeline Quality Gates | Modularize data platform and Airflow DAGs, sanitize notebook credentials, align medallion lakehouse | M1, M2 | DONE |
| M4 | Frontend Architecture & Component Optimization | Modularize `Dashboard.tsx` (554 LOC) and `ClinicalIntelligence.tsx` (466 LOC), zero type errors | M2 | DONE |
| M5 | Performance Budgets & Edge Gateway Hardening | Align Axum edge proxy (cargo check clean), verify performance budgets | M3, M4 | DONE |
| M6 | Full Regression Verification & Forensic Audit | Run 100% backend and frontend test suites, pass Reviewer, Challenger, and Auditor gates | M1-M5 | IN PROGRESS |

---

## Interface Contracts

### 1. Database Model Interfaces (`backend/models/`)
- All foreign key columns must specify `index=True` or be declared inside an explicit `Index('ix_table_col', col)` constraint.
- All high-frequency filtered/sorted queries must have supporting composite indexes.
- All models must be re-exported in `backend/models/__init__.py`.

### 2. Prediction Engine & Calculator Interfaces
- `backend/prediction.py` retains public API route surface and imports from submodules:
  - `backend/services/calculators/`: Deterministic risk equations (FIB-4, MELD, ASCVD, CHA2DS2-VASc, SaMD).
  - `backend/services/ml/`: Model registry, sklearn artifact loading, and SHAP feature attribution.
  - `backend/routes/prediction.py`: FastAPI route handlers with strict Pydantic schemas.
- Route signatures and endpoints (`/predict/{disease}`, `/explain/{disease}`, `/calculators/*`) must remain 100% backward compatible.

### 3. Prompt Registry Interfaces (`backend/prompt_registry.py`)
- Inlined prompts must be registered with typed prompt identifiers (e.g. `CLINICAL_SUMMARY_PROMPT`, `PREDICTION_EXPLANATION_PROMPT`).
- All AI calls obtain prompts via `prompt_registry.get_prompt(name, version=None)`.

### 4. Rust Edge Gateway Licensing State
- `rust_gateway/src/routes/licensing.rs` must manage active license key via thread-safe `Arc<RwLock<LicenseState>>` in `AppState` instead of calling `unsafe { env::set_var }`.

### 5. Frontend Component Modularization
- `Dashboard.tsx` decomposes into:
  - `DashboardMetricsGrid.tsx` (<600 LOC)
  - `DashboardActivityStream.tsx` (<600 LOC)
  - `DashboardQuickActions.tsx` (<600 LOC)
- Pages use TanStack Query hooks (`useDashboardData()`, `usePatients()`) wrapping standard API calls.

---

## Code Layout

```
AI-Healthcare-System/
├── backend/
│   ├── main.py                          # <600 LOC: Application entry point & route registration
│   ├── lifecycle.py                     # Extracted lifespan startup/shutdown diagnostics & migrations
│   ├── core_ai.py                       # Unified AI provider router & semantic cache
│   ├── prompt_registry.py               # Centralized repository for all system prompts
│   ├── database.py                      # DB engine, session factory & SQLite/Postgres dual-mode
│   ├── models/                          # Modular SQLAlchemy ORM models & index declarations
│   ├── schemas/                         # Pydantic V2 request & response schemas
│   ├── routes/                          # Domain route handlers (<600 LOC per file)
│   └── services/                        # Business logic, ML loaders, and clinical calculators
├── frontend/
│   ├── src/
│   │   ├── pages/                       # Page components (<600 LOC per file)
│   │   ├── components/                  # Focused, reusable UI sub-components (<600 LOC)
│   │   ├── hooks/                       # TanStack Query custom data hooks
│   │   └── lib/                         # API clients, utilities, and configuration
├── rust_gateway/
│   └── src/                             # Axum 0.8 edge proxy, SIMD vector store, and routes
├── databricks_notebooks/                # Medallion ETL notebooks (sanitized credentials)
├── airflow/                             # Data engineering DAGs (<600 LOC)
└── tests/                               # Comprehensive pytest automated test suite
```
