# AI Agent Frontend Engineering Playbook

> **Audience:** Autonomous AI Agents (Antigravity, Devin, Codex, GitHub Copilot, Kiro, Google AI Studio) & Autonomous Subagents.
> **Scope:** React 19 view & route discovery, canonical component architecture, responsive overflow protection, and self-healing validation for `apps/web/`.

---

## 1. Core Operating Directive

**DO NOT write inline Tailwind "div soup" cards, guess route paths, or invent custom page shells.**
All user interfaces in AI Healthcare System are governed by canonical templates (`HubPageTemplate`, `RegistryPageLayout`, `UniversalRegistryPage`, `EntityDetailLayout`) and approved primitives (`BentoCard`, `SurfaceCard`, `FeatureCard`, `StatTile`, `TelemetryValue`).

Always interact with the frontend tooling via the canonical Bun CLI commands below. They execute in under 100ms, output token-minimized JSON for LLM context windows, and eliminate UI hallucinations.

---

## 2. CLI Tooling Reference

### A. View & Route Introspection (`frontend:routes`)
Extract all 102 registered views, page components, layout shells, URL parameters, and auth requirements in under 50ms:

```bash
# Return token-minimized JSON of all frontend views
bun run frontend:routes

# Filter by module or path (e.g. characters, tournaments, story, calculators)
bun run frontend:routes --filter characters

# Output as compact markdown table
bun run frontend:routes --format compact
```

### B. Component & Primitive Catalog (`frontend:components`)
Never invent custom card divs or unapproved layouts. Introspect approved design system primitives with import paths, prop types, and copy-pasteable examples:

```bash
# Return full component catalog in token-minimized JSON
bun run frontend:components

# Filter by component name or category (e.g. template, card, metric)
bun run frontend:components --filter card

# Output as human/LLM-readable markdown table with usage snippets
bun run frontend:components --format compact
```

### C. Self-Healing Architecture Guardrails (`frontend:validate`)
Whenever you add or modify a `.tsx` page in `apps/web/src/pages/`, verify component and responsive invariants:

```bash
# Validate full frontend architecture across all 80 pages
bun run frontend:validate

# Validate a single specific page
bun run frontend:validate --target apps/web/src/pages/CharactersList.tsx

# Machine-parseable JSON error diffs with concrete remediation code
bun run frontend:validate --format json
```

#### Self-Healing Protocol:
If `frontend:validate` fails (exit code `1`):
1. Parse the JSON error diff in `violations[]`.
2. Inspect `file`, `line`, `ruleId`, `offendingCode`, and `remediation`.
3. Apply the suggested canonical component or responsive fix (e.g. replacing `<div className="...rounded-...border...bg-...">` with `<BentoCard>`).
4. Re-run `bun run frontend:validate` until status is `PASS` (exit code `0`).

### D. Unified Frontend Verification Harness (`frontend:verify`)
Run the complete 3-stage frontend verification harness (Route Introspection, Component Catalog, and Invariant Linting):

```bash
bun run frontend:verify
```
*Expected result:* 10/10 passing tests in under 1 second.

---

## 3. Canonical Architecture & Invariant Rules

When authoring or editing React components:
1. **Mandatory Canonical Shell (FE-SHELL-001):** Every page component in `apps/web/src/pages/` MUST import and use an approved layout template:
   - Dashboards / Overview Hubs: `<HubPageTemplate>`
   - Lists / Registries / Indexes: `<RegistryPageLayout>` or `<UniversalRegistryPage>`
   - Single Entity Profiles: `<EntityDetailLayout>`
   - Structural / Settings / Tool Pages: `<PageShell>`
2. **Prohibition of Raw Card Divs (FE-RAW-CARD-001):** Never write inline card containers like `<div className="rounded-xl border bg-card p-4">`. Use `<BentoCard>`, `<SurfaceCard>`, or `<FeatureCard>` from `@/components/ui/BentoCard`.
3. **Responsive Overflow Protection (FE-RESP-OVERFLOW-001):** Never use unconstrained `w-screen` inside nested containers. Always use `w-full max-w-full`, and wrap wide data tables in `overflow-x-auto`.
4. **Accessibility (FE-A11Y-001):** All `<img>` tags require descriptive `alt="..."` attributes, and icon-only buttons require `aria-label="..."`.

---
*Playbook maintained for the AI Healthcare System Production Fleet.*
