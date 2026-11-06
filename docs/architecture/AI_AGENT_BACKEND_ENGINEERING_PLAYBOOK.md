# AI Agent Backend Engineering Playbook

> **Audience:** Autonomous AI Agents (Antigravity, Devin, Codex, GitHub Copilot, Kiro, Google AI Studio) & Autonomous Subagents.
> **Scope:** Axum 0.7 API route discovery, schema introspection, in-memory sandbox testing, self-healing contract validation, and unified verification for Universe Dex.

---

## 1. Core Operating Directive

**DO NOT guess Axum routes, hallucinate JSON payloads, or parse thousands of lines of Rust manually.**
All backend APIs in Universe Dex are unified in the 100% pure Rust Axum engine (`crates/server/src/api/`).

Always interact with the backend tooling via the canonical Bun CLI commands below. They execute in under 100ms, output token-minimized JSON for LLM context windows, and guarantee zero route hallucinations.

---

## 2. CLI Tooling Reference

### A. Route Introspection (`backend:routes`)
Extract all 187+ registered Axum routes, HTTP methods, modules, handlers, and security status in under 100ms:

```bash
# Return token-minimized JSON list of all routes (LLM context friendly)
bun run backend:routes

# Filter by specific API module (e.g. characters, biophysics, compute, vs)
bun run backend:routes --filter biophysics

# Human/LLM-readable compact markdown table
bun run backend:routes --format compact
```

### B. Schema Introspection (`backend:schema`)
Introspect exact Rust request/response DTO schemas (field names, types, optionality) without reading Rust structs:

```bash
# Introspect schema for a specific endpoint
bun run backend:schema --route /api/biophysics/validate

# Output schema as markdown table
bun run backend:schema --route /api/biophysics/validate --format compact

# Export all route schemas across the backend
bun run backend:schema --format json
```

### C. Zero-Credential In-Memory Test Sandbox (`UNIVERSEDEX_ENV=test`)
When launching or testing the backend in an autonomous agent environment, **do not require external Postgres or Doppler production secrets**:

```bash
# Set environment flag to boot the in-memory SQLite sandbox with deterministic test fixtures
export UNIVERSEDEX_ENV=test
cargo run --bin universe-dex
```
*Features:*
- Boots in <500ms using in-memory SQLite (`:memory:`).
- Deterministically seeds 30 canonical ranks, core dynasties, places, species entities, and canonical characters.
- Completely isolated from local disk and production databases.

### D. Self-Healing Contract Guardrails (`backend:validate`)
Whenever you add, modify, or refactor an Axum endpoint, verify HTTP contract compliance:

```bash
# Run standalone ephemeral contract validation (zero-process mock mode)
bun run backend:validate --ephemeral

# Machine-parseable JSON error diff with Rust remediation pointers
bun run backend:validate --ephemeral --format json
```

#### Self-Healing Protocol:
If `backend:validate` fails (exit code `1`):
1. Parse the JSON error diff in `violations[]`.
2. Inspect `route`, `expected_status` vs `actual_status`, `missing_fields`, and `remediation`.
3. Apply the exact Rust code fix suggested in `remediation` inside `crates/server/src/api/`.
4. Re-run `bun run backend:validate --ephemeral` until exit code `0` is achieved.

### E. Unified Backend Verification Harness (`backend:verify`)
Run the complete 3-stage backend verification harness (Route Linting, In-Memory Sandbox, Contract Tests, and Cargo Checks):

```bash
bun run backend:verify
```
*Expected result:* 42/42 passing tests in under 10 seconds.

---

## 3. Axum 0.7 Route & Middleware Laws

When writing or modifying Rust backend code:
1. **Security Invariant:** All `/api/*` and `/analytics/*` routes MUST pass through `security_guard_middleware`. Never mount route groups outside the security layer.
2. **Standard Error Envelope:** Always return `api_error(status, message)` matching the uniform `{"status": "error", "error": ...}` JSON schema.
3. **Parameter Syntax:** Axum uses `:param` for path parameters (e.g. `/api/characters/:id`). The introspection engine automatically normalizes this to `{id}` for OpenAPI compatibility.
4. **Deterministic Seeding:** Any new required table fixture must be added to `Database::open_in_memory_seeded()` in `crates/server/src/db/mod.rs`.

---
*Playbook maintained by ENI & LO for the Universe Dex AI Studio Fleet.*
