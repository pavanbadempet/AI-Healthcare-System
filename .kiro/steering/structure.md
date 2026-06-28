# Kiro Steering Structure (.kiro/steering/structure.md)

Steering directives for AI agents executing modifications and upgrades inside the AI Healthcare System repository.

## Instruction Hierarchy

1. **`AGENTS.md` (Root):** Canonical instructions governing all code updates, database policies, environment setups, and security constraints.
2. **Subtree `AGENTS.md`:** Scoped instructions (e.g. `backend/AGENTS.md`, `frontend/AGENTS.md`) holding precedence within their directories.
3. **`CONTEXT.md` Files:** Extended modules list, design documentations, and reference records. Must be referenced only for context.

## Core Behavioral Protocols

- **Rule Checks:** Agents must read `AGENTS.md` at session start.
- **Verification Gates:** Before claiming completion, run the narrowest relevant test suite (`pytest` or `vitest`) and verify that coverage requirements are satisfied.
- **Non-blocking Execution:** Run async commands and background tasks without locking processes. Monitor status notifications instead of polling logs.
- **HIPAA Exception Guards:** Intercept and scrub all tracebacks containing patient metrics or clinical text.
