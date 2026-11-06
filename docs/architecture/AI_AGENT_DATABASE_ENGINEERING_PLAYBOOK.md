# AI Agent Database Engineering Playbook

> **Autonomous Workforce Specification**
> Target Audience: Autonomous AI Agents (Antigravity, Devin, Codex, GitHub Copilot, Kiro)
> Mission: Zero-human-dependency database engineering, schema introspection, ACID invariant validation, self-healing remediation, and migration drift detection for Universe Dex.

---

## 1. Executive Architecture

Universe Dex uses a high-performance relational database architecture powered by SQLite with WAL mode, round-robin `ReaderPool`, Moka caching in Rust (`crates/server/src/db/mod.rs`), and synchronized columnar lakehouse tables.

Because there are **zero human developers**, every AI agent interacting with Universe Dex databases must operate through deterministic, token-minimized, and self-healing interfaces. Any schema discrepancy, broken foreign key, or missing index must be detected and cured autonomously in sub-second time.

```
┌─────────────────────────────────────────────────────────────┐
│                 Autonomous AI Workforce                     │
│          (Antigravity / Devin / Codex / Copilot)             │
└──────────────────────────────┬──────────────────────────────┘
                               │
            ┌──────────────────┴──────────────────┐
            ▼                                     ▼
┌──────────────────────────────┐    ┌──────────────────────────────┐
│  Schema Introspection Engine │    │ Invariant & Health Validator │
│ (scripts/lib/db_schema_...ts)│    │  (scripts/lib/db_validator)  │
│  - 102 tables, 217 indexes   │    │  - DB-FK-001 (Broken FKs)    │
│  - 148 foreign keys          │    │  - DB-FK-002 (Unindexed FKs) │
│  - Introspection in <30ms    │    │  - DB-PRAGMA (WAL & Timeout) │
└──────────────┬───────────────┘    └──────────────┬───────────────┘
               │                                   │
               ├───────────────────┬───────────────┘
               ▼                   ▼
┌──────────────────────────────┐ ┌──────────────────────────────┐
│ Schema Drift & Migration     │ │ Self-Healing Remediation     │
│ (scripts/lib/db_migration...)| │ (bun run db:fix)             │
│ - Canonical SQL Parity       │ │ - Idempotent CREATE INDEX    │
│ - Missing Column Detection   │ │ - Concurrency PRAGMA tuning  │
└──────────────────────────────┘ └──────────────────────────────┘
```

---

## 2. Fast CLI Reference for AI Agents

All commands run via Bun and are registered in `package.json`:

| Command | Purpose | SLA Latency | AI Token Impact |
|---|---|---|---|
| `bun run db:schema` | Introspect live database schema, tables, columns, indexes, and FKs | < 50ms | Markdown summary (compact) |
| `bun run db:schema --table=characters` | Deep dive into a single table's columns, types, foreign keys, and indexes | < 10ms | High-precision single table view |
| `bun run db:schema --format=json --compact` | Machine-readable JSON schema for LLM reasoning | < 50ms | Minimized token JSON payload |
| `bun run db:validate` | Full ACID, foreign key integrity, missing index, and pragma audit | < 50ms | Clean report with remediation SQL |
| `bun run db:validate --format=json` | Machine-parseable JSON violation diff with SQL patches | < 50ms | Pure JSON error diff |
| `bun run db:drift` | Compares live database schema against canonical SQL file | < 60ms | Drift report + ALTER TABLE DDL |
| `bun run db:fix` | Self-heals the database by executing all generated auto-remediation SQL | < 100ms | Zero manual intervention required |
| `bun run db:verify` | Complete 3-stage database verification test harness | < 200ms | Structured PASS/FAIL status |

---

## 3. Database Invariant Catalog

Every autonomous agent modifying schemas, running migrations, or executing queries must respect the following formal invariants:

### Rule 1: `DB-INTEGRITY-001` — B-Tree File Integrity
- **Condition**: `PRAGMA quick_check;` must return `ok`.
- **Severity**: `CRITICAL`.
- **Remediation**: Run full `PRAGMA integrity_check;` and restore clean snapshot if corrupted.

### Rule 2: `DB-FK-001` — Zero Broken Foreign Keys
- **Condition**: `PRAGMA foreign_key_check;` must return 0 rows.
- **Severity**: `HIGH`.
- **Remediation**: Inspect dangling rowid and remove or reconcile orphaned record referencing non-existent parent.

### Rule 3: `DB-FK-002` — Mandatory Foreign Key Indexing
- **Condition**: Every foreign key column (`child.parent_id`) must have an index where it is the leading column.
- **Why**: SQLite acquires full table scans and table locks when parent rows are updated or deleted if the child foreign key column is unindexed.
- **Severity**: `MEDIUM`.
- **Remediation**:
  ```sql
  CREATE INDEX IF NOT EXISTS "idx_{table}_{column}" ON "{table}" ("{column}");
  ```

### Rule 4: `DB-PRAGMA-001` through `003` — Concurrency & Locking
- **Condition**:
  - `PRAGMA journal_mode = WAL;` (Write-Ahead Logging for non-blocking concurrent readers).
  - `PRAGMA foreign_keys = ON;` (Enforce relational constraints on all sessions).
  - `PRAGMA busy_timeout = 5000;` (Eliminates transient `SQLITE_BUSY` errors).
  - `PRAGMA synchronous = NORMAL;` (Optimal durability with 5x-10x write throughput in WAL mode).

### Rule 5: `DB-CANON-001` / `002` — Canonical Seed Table Integrity
- **Condition**: In production/default databases, canonical tables (`characters`, `ranks`, `dynasties`, `places`, `species_ranges`) must exist and contain seeded records.

---

## 4. Self-Healing Workflow for AI Agents

When an AI agent makes schema changes or encounters a database test failure:

```bash
# 1. Run the validator to obtain structured error diff
bun run db:validate --format=json

# 2. Inspect generated autoRemediationSql field
# Example output:
# "autoRemediationSql": [
#   "CREATE INDEX IF NOT EXISTS \"idx_characters_dynasty_id\" ON \"characters\" (\"dynasty_id\");"
# ]

# 3. Apply remediation automatically
bun run db:fix

# 4. Verify all invariants pass
bun run db:verify
```

---

## 5. Verification Harness SLA

The verification suite (`bun test tests/db_platform.test.ts` or `bun run db:verify`) executes:
- 10 automated unit and integration tests.
- Live database schema introspection.
- In-memory SQLite transaction and foreign key validation.
- Missing index detection and self-healing assertion.
- Canonical SQL drift detection.
- **Total Execution Time**: < 400ms (Guaranteed < 5000ms SLA).
