# AI Healthcare System Rewrite Master Plan

## Objectives
1. **R1**: Expand `rust_gateway/` into primary backend server serving 100% of API endpoints from `backend/main.py` (~40 router modules), with dual SQLite/Postgres sqlx support.
2. **R2**: Bun-powered ElysiaJS API Orchestration Layer (BFF proxy, JWT auth, rate limiting, CORS, compression, WebSocket proxying, static serving).
3. **R3**: Native Rust ONNX Runtime ML inference (`ort` crate) for all 5 disease models + stroke/longitudinal with Rust scaler preprocessing (zero Python dependency).
4. **R4**: Frontend zero-breakage compatibility, E2E test verification, Docker and deployment update.

## Execution Topology
```
Project Orchestrator
  │
  ├── Phase 0: Survey (3 Explorers in parallel)
  │     ├── explorer_1: FastAPI routes & contracts survey
  │     ├── explorer_2: rust_gateway & database models survey
  │     └── explorer_3: ML models & ONNX inference survey
  │
  ├── Feature Synthesis & PROJECT.md generation
  │
  ├── Track A: E2E Testing Orchestrator (Tiers 1-4 opaque-box testing)
  │     └── Publishes TEST_READY.md
  │
  └── Track B: Implementation Track
        ├── Milestone 1 Sub-Orch: Rust Database & Models (sqlx SQLite/Postgres)
        ├── Milestone 2 Sub-Orch: Rust ONNX ML Inference Engine & Scalers
        ├── Milestone 3 Sub-Orch: Rust API Coverage (~40 routers + WS)
        ├── Milestone 4 Sub-Orch: Bun ElysiaJS Edge BFF Gateway
        └── Milestone 5 Sub-Orch: Integration, 100% E2E Pass, Tier 5 Adversarial Hardening & Docker/Deploy
```

## Gate Enforcement
Every milestone requires:
- Build & tests pass
- Reviewers APPROVE
- Challengers empirically verify
- Forensic Auditor CLEAN (Binary Veto)
