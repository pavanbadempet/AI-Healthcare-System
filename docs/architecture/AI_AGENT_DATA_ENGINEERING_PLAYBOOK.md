# AI Agent Data Engineering Playbook

> **Audience:** Autonomous AI Agents (Antigravity, Devin, Codex, GitHub Copilot, Kiro, Google AI Studio) & Autonomous Subagents.
> **Scope:** Ground-truth data access, schema introspection, biophysical verification, and storage compaction for AI Healthcare System.

---

## 1. Core Operating Directive

**DO NOT read or parse raw Parquet files, CSV strings, or internal SQLite files directly.** 
All ground-truth data in AI Healthcare System is managed inside the local Delta Lakehouse (`data/lakehouse/main/healthcare_lakehouse/`). 

Always interact with the lakehouse using the canonical Bun + DuckDB CLI commands below. They execute in under 50ms, return token-efficient structured outputs, and automatically filter out tombstoned historical Delta log files.

---

## 2. CLI Tooling Reference

### A. Query Ground Truth (`data:query`)
Query any table using SQL or simple flags without writing custom database connection scripts:

```bash
# Query with simple table flag (defaults to compact markdown table)
bun run data:query --table characters --limit 10

# Return token-minimized JSON for LLM context windows
bun run data:query --table characters --limit 5 --format json

# Execute arbitrary analytical SQL queries with projection pushdown
bun run data:query --sql "SELECT id, name, height_cm, weight_kg, rank_number FROM characters WHERE rank_number <= 5"
```

### B. Schema Introspection (`data:schema`)
Never guess table schemas or column names. Introspect any table or the entire 87-table catalog in sub-second time:

```bash
# Introspect a single table
bun run data:schema --table characters

# Introspect all 87 tables into JSON
bun run data:schema --format json
```

### C. Biophysical & Relational Invariant Validation (`data:validate`)
Whenever you add, modify, or mutate character, species, or territory data, you **MUST** run the validation suite to prevent agent drift and canonical corruption:

```bash
# Validate full lakehouse integrity
bun run data:validate

# Machine-parseable JSON error diagnostics with remediation SQL
bun run data:validate --format json
```

#### Self-Healing Protocol:
If `data:validate` fails (exit code `1`):
1. Parse the JSON error diff in `violations[]`.
2. Inspect `failing_row_id`, `rule_id`, and `remediation_sql`.
3. Execute the provided `remediation_sql` or correct the source data accordingly.
4. Re-run `bun run data:validate` until exit code `0` is achieved.

### D. Lakehouse Compaction & Hygiene (`data:compact`)
When modifying data or after batch synchronization, run compaction to consolidate fragmented Parquet files and prune tombstones:

```bash
# Preview compaction impact (dry run)
bun run data:compact --table characters --dryRun

# Compact and vacuum obsolete tombstone files
bun run data:compact --table characters --vacuum

# Compact all tables across the lakehouse
bun run data:compact --all --vacuum
```

### E. Unified Test Verification (`data:verify`)
Run the complete 29-test end-to-end verification harness:

```bash
bun run data:verify
```
*Expected result:* 29/29 passing tests in under 5 seconds.

---

## 3. Canonical Biophysical Invariants

When writing code or generating characters, adhere strictly to these physical laws:
1. **Allometric Mass Envelope:** $M_{\text{baseline}} = 13.25 \cdot H^{3.02}$ (mass ratio strictly bounded in $[0.55, 1.85]$).
2. **Mortal Male Ceiling:** Males are strictly capped at **Rank 21** and mortal stature ($\le 180\text{ cm}$). Zero male Exults.
3. **Maternal Precedence:** Surnames and divine inheritance follow maternal descent ($t \ge T_{\text{mother}} - 1$).
4. **Relational Integrity:** All `mother_id` and `father_id` references must resolve to valid characters or remain `NULL`.

---
*Playbook maintained for the AI Healthcare System Production Fleet.*
