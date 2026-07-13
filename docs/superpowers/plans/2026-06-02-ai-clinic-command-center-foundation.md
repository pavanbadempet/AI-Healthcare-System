# AI Clinic Command Center Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the existing product demo-ready and trustworthy before adding the clinic visit workspace.

**Architecture:** This plan adds a small PHI-safe demo readiness endpoint, typed frontend API failure handling, buyer-safe dashboard degraded states, and claim-language cleanup. It keeps the current FastAPI + Next.js structure and avoids introducing a new visit domain model until the foundation is green.

**Tech Stack:** FastAPI, SQLAlchemy test fixtures, pytest, Next.js 16 App Router, React 19, TypeScript, Jest, Testing Library.

---

## Scope

This plan implements the Week 1 foundation from `docs/superpowers/specs/2026-06-02-ai-clinic-command-center-design.md`.

It does not build the full clinic visit workspace. That gets a separate plan after this foundation passes.

## File Structure

Create:

- `backend/demo_readiness.py`: PHI-safe demo/pilot readiness report endpoint.
- `tests/unit/test_demo_readiness.py`: backend readiness endpoint tests.
- `frontend/src/lib/apiErrors.ts`: typed frontend API failure helpers.
- `frontend/src/components/system/DemoReadinessBadge.tsx`: compact readiness indicator for buyer-facing pages.
- `frontend/src/components/system/DegradedStateBanner.tsx`: reusable frontend degraded-state banner.

Modify:

- `backend/main.py`: mount the demo readiness router.
- `frontend/src/lib/api.ts`: use typed API connection errors and add `getDemoReadiness()`.
- `frontend/src/lib/useTelemetry.ts`: avoid noisy console errors and expose clean status state.
- `frontend/jest.setup.ts`: mock canvas and ResizeObserver for stable component tests.
- `frontend/src/app/login/page.tsx`: remove unsupported and misspelled compliance claim.
- `frontend/src/app/signup/page.tsx`: remove unsupported compliance claim.
- `frontend/src/components/layout/TopNav.tsx`: remove unsupported compliance, uptime, encryption, and accuracy claims.
- `frontend/src/app/(p)/dashboard/page.tsx`: show clinic/demo readiness and clean degraded states.
- `frontend/src/app/(p)/infrastructure/page.tsx`: remove fake uptime claim.
- `frontend/src/components/operations/OperationsCockpit.tsx`: make backend failure buyer-safe.
- `frontend/src/components/operations/PatientDiagnosticResults.tsx`: add patient-facing clinician disclaimer.
- `frontend/src/components/operations/PatientCareTimeline.tsx`: fix wording typo and align sync wording.
- `frontend/src/app/(p)/patients/[id]/page.tsx`: restore patient-detail AI synthesis safety copy.
- `frontend/src/__tests__/*.tsx`: update stale assertions and add safety checks for readiness/degraded states.

---

### Task 1: Stabilize Frontend Test Harness

**Files:**

- Modify: `frontend/jest.setup.ts`
- Modify: `frontend/src/__tests__/TopNav.test.tsx`

- [ ] **Step 1: Replace Jest setup with DOM API mocks**

Replace the full contents of `frontend/jest.setup.ts` with:

```ts
import '@testing-library/jest-dom';

Object.defineProperty(HTMLCanvasElement.prototype, 'getContext', {
  configurable: true,
  value: jest.fn(() => ({
    clearRect: jest.fn(),
    beginPath: jest.fn(),
    moveTo: jest.fn(),
    lineTo: jest.fn(),
    stroke: jest.fn(),
    fill: jest.fn(),
    arc: jest.fn(),
    closePath: jest.fn(),
    fillText: jest.fn(),
    measureText: jest.fn(() => ({ width: 0 })),
    createLinearGradient: jest.fn(() => ({
      addColorStop: jest.fn(),
    })),
  })),
});

class MockResizeObserver {
  observe = jest.fn();
  unobserve = jest.fn();
  disconnect = jest.fn();
}

Object.defineProperty(window, 'ResizeObserver', {
  configurable: true,
  value: MockResizeObserver,
});
```

- [ ] **Step 2: Remove trailing whitespace in TopNav test**

In `frontend/src/__tests__/TopNav.test.tsx`, remove trailing spaces from the blank lines inside the three tests. The first test should read:

```ts
  it('renders the TopNav logo and title', () => {
    (usePathname as jest.Mock).mockReturnValue('/');

    render(<TopNav />);

    // The title spans "AI Healthcare System"
    expect(screen.getByText(/AI Healthcare/i)).toBeInTheDocument();
    expect(screen.getByText(/System/i)).toBeInTheDocument();
  });
```

- [ ] **Step 3: Run the narrow harness check**

Run:

```bash
npm --prefix frontend test -- --runInBand src/__tests__/TopNav.test.tsx
```

Expected: the test file passes without canvas or ResizeObserver errors.

- [ ] **Step 4: Commit**

```bash
git add frontend/jest.setup.ts frontend/src/__tests__/TopNav.test.tsx
git commit -m "test: stabilize frontend DOM test harness"
```

---

### Task 2: Add Typed Frontend API Failure Handling

**Files:**

- Create: `frontend/src/lib/apiErrors.ts`
- Modify: `frontend/src/lib/api.ts`
- Test: `frontend/src/__tests__/OperationsCockpit.test.tsx`

- [ ] **Step 1: Create API error helpers**

Create `frontend/src/lib/apiErrors.ts`:

```ts
export class ApiConnectionError extends Error {
  path: string;

  constructor(path: string, causeMessage: string) {
    super(`Backend unavailable for ${path}: ${causeMessage}`);
    this.name = 'ApiConnectionError';
    this.path = path;
  }
}

export function isApiConnectionError(error: unknown): error is ApiConnectionError {
  return error instanceof ApiConnectionError;
}

export function safeApiMessage(error: unknown, fallback: string): string {
  if (isApiConnectionError(error)) {
    return 'Backend service is unavailable. Demo data and cached context remain safe to inspect.';
  }
  if (error instanceof Error && error.message.trim()) {
    return error.message;
  }
  return fallback;
}
```

- [ ] **Step 2: Wire `apiFetch()` to throw typed connection errors**

In `frontend/src/lib/api.ts`, add this import near the top:

```ts
import { ApiConnectionError } from './apiErrors';
```

Replace the start of `apiFetch()` with:

```ts
async function apiFetch<T>(path: string, options: RequestInit = {}): Promise<T> {
  let res: Response;

  try {
    res = await fetch(`${API_BASE}${path}`, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...authHeaders(),
        ...(options.headers || {}),
      },
    });
  } catch (error) {
    throw new ApiConnectionError(path, error instanceof Error ? error.message : 'network request failed');
  }

  if (!res.ok) {
```

Keep the existing non-OK response handling and `return res.json();` unchanged.

- [ ] **Step 3: Update operations cockpit to use safe API copy**

In `frontend/src/components/operations/OperationsCockpit.tsx`, add:

```ts
import { safeApiMessage } from "@/lib/apiErrors";
```

Replace the existing catch block:

```ts
      .catch((err) => setError(err.message || "Failed to load operations cockpit"))
```

with:

```ts
      .catch((err) => setError(safeApiMessage(err, "Operations cockpit is temporarily unavailable")))
```

- [ ] **Step 4: Add degraded-state assertion**

In `frontend/src/__tests__/OperationsCockpit.test.tsx`, add this test after the admin metrics test:

```tsx
  it('shows buyer-safe degraded copy when the backend is unavailable', async () => {
    (getAdminOperationsCockpit as jest.Mock).mockRejectedValueOnce(
      new Error('Backend service is unavailable. Demo data and cached context remain safe to inspect.')
    );

    await renderCockpit();

    expect(await screen.findByRole('alert')).toHaveTextContent(
      'Backend service is unavailable. Demo data and cached context remain safe to inspect.'
    );
  });
```

- [ ] **Step 5: Run the focused test**

Run:

```bash
npm --prefix frontend test -- --runInBand src/__tests__/OperationsCockpit.test.tsx
```

Expected: OperationsCockpit tests pass or fail only on stale display-copy assertions that Task 6 updates.

- [ ] **Step 6: Commit**

```bash
git add frontend/src/lib/apiErrors.ts frontend/src/lib/api.ts frontend/src/components/operations/OperationsCockpit.tsx frontend/src/__tests__/OperationsCockpit.test.tsx
git commit -m "feat: add buyer-safe API degraded states"
```

---

### Task 3: Add Backend Demo Readiness Endpoint

**Files:**

- Create: `backend/demo_readiness.py`
- Modify: `backend/main.py`
- Test: `tests/unit/test_demo_readiness.py`

- [ ] **Step 1: Write backend tests first**

Create `tests/unit/test_demo_readiness.py`:

```py
def test_demo_readiness_reports_demo_ready_without_external_keys(client, monkeypatch):
    monkeypatch.setenv("ABDM_DEMO_MODE", "true")
    monkeypatch.setenv("DATABASE_URL", "sqlite:///./healthcare.db")
    monkeypatch.setenv("SECRET_KEY", "test-secret")
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

    response = client.get("/demo-readiness")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "demo-ready"
    assert body["mode"] == "synthetic-demo"
    assert body["synthetic_data_only"] is True
    assert "GOOGLE_API_KEY" not in str(body)
    assert "test-secret" not in str(body)


def test_demo_readiness_reports_production_blocked_for_unconfigured_runtime(client, monkeypatch):
    monkeypatch.delenv("ABDM_DEMO_MODE", raising=False)
    monkeypatch.setenv("DATABASE_URL", "sqlite:///./healthcare.db")
    monkeypatch.delenv("SECRET_KEY", raising=False)

    response = client.get("/demo-readiness")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "production-blocked"
    assert "Enable ABDM_DEMO_MODE or DEMO_MODE for synthetic demos." in body["blocking_reasons"]
    assert "Configure SECRET_KEY before pilot or production use." in body["blocking_reasons"]
```

- [ ] **Step 2: Run tests to verify failure**

Run:

```bash
python -m pytest tests/unit/test_demo_readiness.py -q
```

Expected: FAIL because `/demo-readiness` is not registered.

- [ ] **Step 3: Add readiness endpoint**

Create `backend/demo_readiness.py`:

```py
"""PHI-safe demo and pilot readiness reporting."""

from __future__ import annotations

import os
from typing import Any

from fastapi import APIRouter

router = APIRouter(prefix="/demo-readiness", tags=["Demo Readiness"])


def _env_bool(name: str) -> bool:
    return os.getenv(name, "").strip().lower() in {"1", "true", "yes", "on"}


def _database_is_sqlite(database_url: str | None) -> bool:
    return bool(database_url and database_url.strip().lower().startswith("sqlite"))


def build_demo_readiness() -> dict[str, Any]:
    database_url = os.getenv("DATABASE_URL")
    demo_mode = _env_bool("ABDM_DEMO_MODE") or _env_bool("DEMO_MODE")
    secret_configured = bool(os.getenv("SECRET_KEY"))
    ai_provider_configured = any(
        bool(os.getenv(name))
        for name in ("GOOGLE_API_KEY", "OPENAI_API_KEY", "ANTHROPIC_API_KEY")
    )

    checks = {
        "synthetic_demo_mode": demo_mode,
        "database_configured": bool(database_url),
        "database_uses_managed_store": bool(database_url and not _database_is_sqlite(database_url)),
        "secret_key_configured": secret_configured,
        "external_ai_optional": True,
        "external_ai_configured": ai_provider_configured,
    }

    blocking_reasons: list[str] = []
    if not demo_mode:
        blocking_reasons.append("Enable ABDM_DEMO_MODE or DEMO_MODE for synthetic demos.")
    if not secret_configured:
        blocking_reasons.append("Configure SECRET_KEY before pilot or production use.")
    if not database_url:
        blocking_reasons.append("Configure DATABASE_URL before pilot or production use.")

    if demo_mode and secret_configured and database_url:
        status = "demo-ready"
        mode = "synthetic-demo"
    elif not blocking_reasons and database_url and not _database_is_sqlite(database_url):
        status = "pilot-ready"
        mode = "configured-pilot"
    else:
        status = "production-blocked"
        mode = "configuration-review"

    return {
        "status": status,
        "mode": mode,
        "synthetic_data_only": demo_mode,
        "blocking_reasons": blocking_reasons,
        "checks": checks,
        "clinical_safety_note": (
            "Demo readiness is operational metadata only. "
            "It does not certify clinical, legal, regulatory, or production readiness."
        ),
    }


@router.get("")
def get_demo_readiness() -> dict[str, Any]:
    return build_demo_readiness()
```

- [ ] **Step 4: Mount router in main app**

In `backend/main.py`, extend the imports:

```py
from . import models, database, auth, chat, explanation, prediction, report, admin, payments, security, telemetry, sales_readiness, hospital_operations, monitoring, diagnostics, pharmacy, billing, discharge, nursing, care_events, interoperability, demo_readiness
```

Add the router after `app.include_router(interoperability.router)`:

```py
app.include_router(demo_readiness.router)
```

- [ ] **Step 5: Run backend readiness tests**

Run:

```bash
python -m pytest tests/unit/test_demo_readiness.py -q
```

Expected: `2 passed`.

- [ ] **Step 6: Commit**

```bash
git add backend/demo_readiness.py backend/main.py tests/unit/test_demo_readiness.py
git commit -m "feat: add demo readiness endpoint"
```

---

### Task 4: Expose Demo Readiness In The Frontend

**Files:**

- Modify: `frontend/src/lib/api.ts`
- Create: `frontend/src/components/system/DemoReadinessBadge.tsx`
- Create: `frontend/src/components/system/DegradedStateBanner.tsx`
- Test: `frontend/src/__tests__/DashboardReadiness.test.tsx`

- [ ] **Step 1: Add frontend API types**

Append this to `frontend/src/lib/api.ts` after the admin operations cockpit functions:

```ts
export type DemoReadinessStatus = 'demo-ready' | 'pilot-ready' | 'production-blocked';

export interface DemoReadiness {
  status: DemoReadinessStatus;
  mode: string;
  synthetic_data_only: boolean;
  blocking_reasons: string[];
  checks: Record<string, boolean>;
  clinical_safety_note: string;
}

export async function getDemoReadiness(): Promise<DemoReadiness> {
  return apiFetch('/demo-readiness');
}
```

- [ ] **Step 2: Create readiness badge**

Create `frontend/src/components/system/DemoReadinessBadge.tsx`:

```tsx
"use client";

import { ShieldCheck, ShieldAlert } from "lucide-react";
import type { DemoReadiness } from "@/lib/api";

interface DemoReadinessBadgeProps {
  readiness: DemoReadiness | null;
  loading?: boolean;
  error?: string;
}

const labelByStatus = {
  "demo-ready": "Demo Ready",
  "pilot-ready": "Pilot Ready",
  "production-blocked": "Production Blocked",
} as const;

export default function DemoReadinessBadge({ readiness, loading = false, error = "" }: DemoReadinessBadgeProps) {
  if (loading) {
    return (
      <span className="status-badge status-badge-accent font-mono text-[9px] uppercase">
        Checking readiness...
      </span>
    );
  }

  if (error || !readiness) {
    return (
      <span className="status-badge border-[var(--warning-border)] bg-[var(--warning-muted)] text-[var(--warning)] font-mono text-[9px] uppercase">
        <ShieldAlert size={11} aria-hidden="true" />
        Readiness Unknown
      </span>
    );
  }

  const isReady = readiness.status === "demo-ready" || readiness.status === "pilot-ready";

  return (
    <span
      className={`status-badge font-mono text-[9px] uppercase ${
        isReady
          ? "border-[var(--success-border)] bg-[var(--success-muted)] text-[var(--success)]"
          : "border-[var(--danger-border)] bg-[var(--danger-muted)] text-[var(--danger)]"
      }`}
      title={readiness.clinical_safety_note}
    >
      {isReady ? <ShieldCheck size={11} aria-hidden="true" /> : <ShieldAlert size={11} aria-hidden="true" />}
      {labelByStatus[readiness.status]}
    </span>
  );
}
```

- [ ] **Step 3: Create degraded state banner**

Create `frontend/src/components/system/DegradedStateBanner.tsx`:

```tsx
"use client";

import { AlertTriangle } from "lucide-react";

interface DegradedStateBannerProps {
  title: string;
  message: string;
}

export default function DegradedStateBanner({ title, message }: DegradedStateBannerProps) {
  return (
    <div
      className="rounded border border-[var(--warning-border)] bg-[var(--warning-muted)] px-4 py-3 text-xs font-mono text-[var(--warning)] uppercase tracking-wide"
      role="status"
    >
      <div className="flex items-start gap-2">
        <AlertTriangle size={14} className="mt-0.5 shrink-0" aria-hidden="true" />
        <div>
          <p className="font-bold">{title}</p>
          <p className="mt-1 text-[var(--text-secondary)]">{message}</p>
        </div>
      </div>
    </div>
  );
}
```

- [ ] **Step 4: Write dashboard readiness test**

Create `frontend/src/__tests__/DashboardReadiness.test.tsx`:

```tsx
import { act, render, screen } from '@testing-library/react';
import DashboardPage from '@/app/(p)/dashboard/page';

jest.mock('next/link', () => function MockLink({ href, children }: { href: string; children: React.ReactNode }) {
  return <a href={href}>{children}</a>;
});

jest.mock('framer-motion', () => ({
  motion: {
    div: ({ children, ...props }: { children?: React.ReactNode; [key: string]: unknown }) => <div>{children}</div>,
  },
}));

jest.mock('recharts', () => ({
  ResponsiveContainer: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  AreaChart: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  XAxis: () => <div />,
  YAxis: () => <div />,
  Tooltip: () => <div />,
  Area: () => <div />,
}));

jest.mock('@/lib/auth', () => ({
  useAuthStore: () => ({ user: { id: 1, username: 'admin', full_name: 'Dr. Admin', role: 'admin' } }),
}));

jest.mock('@/lib/useTelemetry', () => ({
  useTelemetry: () => ({ data: null, status: 'error' }),
}));

jest.mock('@/components/operations/OperationsCockpit', () => function MockOperationsCockpit() {
  return <div>Operations cockpit</div>;
});

jest.mock('@/lib/api', () => ({
  getRecords: jest.fn(() => Promise.reject(new Error('Backend service is unavailable. Demo data and cached context remain safe to inspect.'))),
  getDemoReadiness: jest.fn(() => Promise.resolve({
    status: 'demo-ready',
    mode: 'synthetic-demo',
    synthetic_data_only: true,
    blocking_reasons: [],
    checks: { synthetic_demo_mode: true },
    clinical_safety_note: 'Demo readiness is operational metadata only.',
  })),
}));

describe('Dashboard readiness and degraded states', () => {
  it('shows demo readiness and buyer-safe backend degraded copy', async () => {
    render(<DashboardPage />);

    await act(async () => {
      await Promise.resolve();
    });

    expect(await screen.findByText('Demo Ready')).toBeInTheDocument();
    expect(screen.getByText('Clinic Data Degraded')).toBeInTheDocument();
    expect(screen.getByText(/Backend service is unavailable/i)).toBeInTheDocument();
    expect(screen.queryByText(/99\.999/)).not.toBeInTheDocument();
    expect(screen.queryByText(/98\.4/)).not.toBeInTheDocument();
  });
});
```

- [ ] **Step 5: Run test to verify failure**

Run:

```bash
npm --prefix frontend test -- --runInBand src/__tests__/DashboardReadiness.test.tsx
```

Expected: FAIL because the dashboard does not use `getDemoReadiness()` or the new degraded banner yet.

- [ ] **Step 6: Commit test and new components after Task 5 implementation**

This task's commit happens after Task 5 wires these components into the dashboard.

---

### Task 5: Make Dashboard Buyer-Safe

**Files:**

- Modify: `frontend/src/app/(p)/dashboard/page.tsx`
- Modify: `frontend/src/app/(p)/infrastructure/page.tsx`
- Modify: `frontend/src/lib/useTelemetry.ts`
- Test: `frontend/src/__tests__/DashboardReadiness.test.tsx`

- [ ] **Step 1: Import readiness and degraded-state helpers**

In `frontend/src/app/(p)/dashboard/page.tsx`, replace the API import with:

```ts
import { getDemoReadiness, getRecords, type DemoReadiness, type HealthRecord } from "@/lib/api";
import { safeApiMessage } from "@/lib/apiErrors";
```

Add these imports:

```ts
import DemoReadinessBadge from "@/components/system/DemoReadinessBadge";
import DegradedStateBanner from "@/components/system/DegradedStateBanner";
```

- [ ] **Step 2: Add readiness and record error state**

Inside `DashboardPage()`, after the existing `loading` state, add:

```ts
  const [recordError, setRecordError] = useState("");
  const [readiness, setReadiness] = useState<DemoReadiness | null>(null);
  const [readinessLoading, setReadinessLoading] = useState(true);
  const [readinessError, setReadinessError] = useState("");
```

Replace the records effect with:

```ts
  useEffect(() => {
    setRecordError("");
    getRecords()
      .then(setRecords)
      .catch((err) => setRecordError(safeApiMessage(err, "Clinic records are temporarily unavailable")))
      .finally(() => setLoading(false));
  }, []);
```

Add this readiness effect after it:

```ts
  useEffect(() => {
    setReadinessLoading(true);
    setReadinessError("");
    getDemoReadiness()
      .then(setReadiness)
      .catch((err) => setReadinessError(safeApiMessage(err, "Readiness status is temporarily unavailable")))
      .finally(() => setReadinessLoading(false));
  }, []);
```

- [ ] **Step 3: Remove fake uptime and fake accuracy**

Replace:

```tsx
          <span>UPTIME: 99.999%</span>
```

with:

```tsx
          <DemoReadinessBadge readiness={readiness} loading={readinessLoading} error={readinessError} />
```

Replace the predictive models card object:

```ts
          {
            title: "PREDICTIVE MODELS",
            value: "98.4%",
            sub: "Global Accuracy",
            icon: BrainCircuit,
            trend: "STABLE",
            trendColor: "text-[var(--success)]",
            meta: `Running: ${telemetry ? telemetry.ai_nodes_active : 14} Nodes`,
          },
```

with:

```ts
          {
            title: "AI REVIEW QUEUE",
            value: highRiskRecords.length.toString(),
            sub: "Clinician review required",
            icon: BrainCircuit,
            trend: highRiskRecords.length > 0 ? "REVIEW" : "CLEAR",
            trendColor: highRiskRecords.length > 0 ? "text-[var(--warning)]" : "text-[var(--success)]",
            meta: telemetry ? `AI Nodes: ${telemetry.ai_nodes_active}` : "Demo fallback",
          },
```

Replace the capacity fallback:

```ts
    : 84;
```

with:

```ts
    : 0;
```

Replace the active census fallback metadata:

```ts
            trend: telemetry ? `${telemetry.active_census}/${telemetry.total_capacity}` : "+12",
            trendColor: capacityPct > 85 ? "text-[var(--danger)]" : "text-[var(--warning)]",
            meta: telemetry ? `ED Boarding: ${telemetry.ed_boarding}` : "ICU: 42/50",
```

with:

```ts
            trend: telemetry ? `${telemetry.active_census}/${telemetry.total_capacity}` : "OFFLINE",
            trendColor: telemetry && capacityPct > 85 ? "text-[var(--danger)]" : "text-[var(--text-dim)]",
            meta: telemetry ? `Queue: ${telemetry.ed_boarding}` : "Awaiting backend",
```

- [ ] **Step 4: Add clean degraded banner**

Add this block immediately before `<OperationsCockpit />`:

```tsx
      {(recordError || wsStatus === "error" || wsStatus === "disconnected") && (
        <DegradedStateBanner
          title="Clinic Data Degraded"
          message={recordError || "Telemetry stream is offline. Synthetic demo context remains available."}
        />
      )}
```

- [ ] **Step 5: Make telemetry parse failures quiet**

In `frontend/src/lib/useTelemetry.ts`, replace:

```ts
          } catch {
            console.error("[Telemetry] Failed to parse message");
          }
```

with:

```ts
          } catch {
            setStatus("error");
          }
```

- [ ] **Step 6: Remove infrastructure fake uptime**

In `frontend/src/app/(p)/infrastructure/page.tsx`, replace:

```tsx
          <span className="hidden sm:inline">UPTIME: 99.999%</span>
```

with:

```tsx
          <span className="hidden sm:inline">READINESS: REVIEW REQUIRED</span>
```

- [ ] **Step 7: Run dashboard readiness test**

Run:

```bash
npm --prefix frontend test -- --runInBand src/__tests__/DashboardReadiness.test.tsx
```

Expected: PASS.

- [ ] **Step 8: Commit Tasks 4 and 5 together**

```bash
git add frontend/src/lib/api.ts frontend/src/components/system/DemoReadinessBadge.tsx frontend/src/components/system/DegradedStateBanner.tsx 'frontend/src/app/(p)/dashboard/page.tsx' 'frontend/src/app/(p)/infrastructure/page.tsx' frontend/src/lib/useTelemetry.ts frontend/src/__tests__/DashboardReadiness.test.tsx
git commit -m "feat: surface demo readiness on dashboard"
```

---

### Task 6: Remove Unsupported Frontend Claims

**Files:**

- Modify: `frontend/src/app/login/page.tsx`
- Modify: `frontend/src/app/signup/page.tsx`
- Modify: `frontend/src/components/layout/TopNav.tsx`
- Test: `frontend/src/__tests__/ComplianceCopy.test.tsx`
- Test: `frontend/src/__tests__/ChatScope.test.tsx`

- [ ] **Step 1: Confirm compliance copy test fails before cleanup**

Run:

```bash
npm --prefix frontend test -- --runInBand src/__tests__/ComplianceCopy.test.tsx src/__tests__/ChatScope.test.tsx
```

Expected: FAIL because visible copy includes unsupported `HIPAA`, `E2E`, or hard-coded accuracy claims.

- [ ] **Step 2: Replace login claim chips**

In `frontend/src/app/login/page.tsx`, replace the three chip labels:

```tsx
              <span className="w-1.5 h-1.5 bg-[var(--accent-emerald)] rounded-full" /> HIPPA-Safe
```

with:

```tsx
              <span className="w-1.5 h-1.5 bg-[var(--accent-emerald)] rounded-full" /> Privacy-Ready
```

Replace:

```tsx
              <span className="w-1.5 h-1.5 bg-[var(--accent)] rounded-full" /> JWT Encrypted
```

with:

```tsx
              <span className="w-1.5 h-1.5 bg-[var(--accent)] rounded-full" /> JWT Session
```

Keep `Audit Active`.

- [ ] **Step 3: Replace signup compliance claim**

In `frontend/src/app/signup/page.tsx`, replace:

```tsx
              { icon: ShieldCheck, text: "HIPAA-grade access boundaries" },
```

with:

```tsx
              { icon: ShieldCheck, text: "Role-scoped access boundaries" },
```

- [ ] **Step 4: Replace TopNav unsupported claims**

In `frontend/src/components/layout/TopNav.tsx`, replace the telemedicine `longDesc`:

```ts
      "HIPAA-grade telemedicine portal. Initiate secure video consultations, manage appointment queues, and access remote patient encounter notes.",
```

with:

```ts
      "Clinician-led telemedicine workspace. Manage consultation queues, appointment notes, and remote encounter context with role-scoped access.",
```

Replace telemedicine highlights:

```ts
    highlights: ["Live Rooms", "E2E Encrypted"],
```

with:

```ts
    highlights: ["Live Rooms", "Role Scoped"],
```

Replace cardiology highlights:

```ts
    highlights: ["ML v2.1", "Ensemble", "98.4% Accuracy"],
```

with:

```ts
    highlights: ["Model Card", "Review Required", "Screening Support"],
```

Replace AI assistant highlights:

```ts
    highlights: ["Online", "Context-Aware", "HIPAA Safe"],
```

with:

```ts
    highlights: ["Online", "Context-Aware", "Clinician Review"],
```

- [ ] **Step 5: Run source claim scan**

Run:

```bash
rg -n "HIPAA|HIPPA|E2E Encrypted|98\\.4% Accuracy|HIPAA Safe|99\\.999" frontend/src/app frontend/src/components
```

Expected: no matches in frontend app or component source files.

- [ ] **Step 6: Commit**

```bash
git add frontend/src/app/login/page.tsx frontend/src/app/signup/page.tsx frontend/src/components/layout/TopNav.tsx frontend/src/__tests__/ComplianceCopy.test.tsx frontend/src/__tests__/ChatScope.test.tsx
git commit -m "chore: remove unsupported frontend claims"
```

---

### Task 7: Restore Patient-Facing Clinical Safety Copy

**Files:**

- Modify: `frontend/src/components/operations/PatientDiagnosticResults.tsx`
- Modify: `frontend/src/components/operations/PatientCareTimeline.tsx`
- Modify: `frontend/src/app/(p)/patients/[id]/page.tsx`
- Test: `frontend/src/__tests__/PatientDiagnosticResults.test.tsx`
- Test: `frontend/src/__tests__/PatientCareTimeline.test.tsx`
- Test: `frontend/src/__tests__/ComplianceCopy.test.tsx`

- [ ] **Step 1: Run focused tests to verify failures**

Run:

```bash
npm --prefix frontend test -- --runInBand src/__tests__/PatientDiagnosticResults.test.tsx src/__tests__/PatientCareTimeline.test.tsx src/__tests__/ComplianceCopy.test.tsx
```

Expected: FAIL on missing diagnostic disclaimer, stale sync wording, and patient-detail AI synthesis copy.

- [ ] **Step 2: Add diagnostic disclaimer**

In `frontend/src/components/operations/PatientDiagnosticResults.tsx`, add this block inside the `<div className="p-4 space-y-3">`, immediately after the released-results count row:

```tsx
        <div className="rounded border border-[var(--warning-border)] bg-[var(--warning-muted)] px-3 py-2 text-[10px] font-mono uppercase text-[var(--warning)]">
          Patients should consult a qualified clinician for diagnosis, treatment, follow-up, or emergencies. Released diagnostics are clinician-reviewed records, not autonomous AI advice.
        </div>
```

- [ ] **Step 3: Fix care timeline typo**

In `frontend/src/components/operations/PatientCareTimeline.tsx`, replace:

```tsx
              Timeline access is limited to authorized clinicial operators.
```

with:

```tsx
              Timeline access is limited to authorized clinical operators.
```

- [ ] **Step 4: Restore patient-detail AI synthesis safety copy**

In `frontend/src/app/(p)/patients/[id]/page.tsx`, replace:

```tsx
              <h3 className="section-label mb-3">Intelligence Synthesis</h3>
```

with:

```tsx
              <h3 className="section-label mb-3">Clinical AI Synthesis</h3>
```

Replace the contents of the synthesis text block:

```tsx
              <div className="text-xs font-mono text-[var(--text-secondary)] space-y-3 leading-relaxed uppercase">
                <p>
                  <strong>AI DRAFT STATUS:</strong> Awaiting clinicial review.
                </p>
                <p>
                  <strong>PROTOCOL CHECKLIST:</strong><br />
                  1. Load verified diagnostics from HL7 feed.<br />
                  2. Review RAG embeddings reference databases.<br />
                  3. Sign off independent assessment record.
                </p>
                <p className="text-[var(--warning)] leading-relaxed">
                  Support active: AI output is draft context. Clinician review required for diagnostics and treatment. Emergencies escalate immediately.
                </p>
              </div>
```

with:

```tsx
              <div className="text-xs font-mono text-[var(--text-secondary)] space-y-3 leading-relaxed uppercase">
                <p>
                  <strong>AI DRAFT STATUS:</strong> Awaiting clinician review.
                </p>
                <p>
                  <strong>SAFETY BOUNDARY:</strong> Decision support only. This is not a diagnosis or treatment plan.
                </p>
                <p>
                  <strong>REVIEW SEQUENCE:</strong><br />
                  1. Load verified source data.<br />
                  2. Prepare clinician-reviewed summary context.<br />
                  3. Doctor edits and signs final note.
                </p>
                <p className="text-[var(--warning)] leading-relaxed">
                  Consult a qualified clinician for diagnosis, treatment, follow-up, or emergencies. Escalate emergency symptoms to urgent care immediately.
                </p>
              </div>
```

- [ ] **Step 5: Align care timeline assertions**

In `frontend/src/__tests__/PatientCareTimeline.test.tsx`, replace each stale sync assertion:

```ts
    expect(screen.getByText('Synced through event #12')).toBeInTheDocument();
```

with:

```ts
    expect(screen.getByText('Synced Event ID: #12')).toBeInTheDocument();
```

Make the same replacement for `#13` and `#14`.

- [ ] **Step 6: Run focused tests**

Run:

```bash
npm --prefix frontend test -- --runInBand src/__tests__/PatientDiagnosticResults.test.tsx src/__tests__/PatientCareTimeline.test.tsx src/__tests__/ComplianceCopy.test.tsx
```

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add frontend/src/components/operations/PatientDiagnosticResults.tsx frontend/src/components/operations/PatientCareTimeline.tsx 'frontend/src/app/(p)/patients/[id]/page.tsx' frontend/src/__tests__/PatientDiagnosticResults.test.tsx frontend/src/__tests__/PatientCareTimeline.test.tsx frontend/src/__tests__/ComplianceCopy.test.tsx
git commit -m "fix: restore patient-facing clinical safety copy"
```

---

### Task 8: Align Stale Operations Tests With Current Copy

**Files:**

- Modify: `frontend/src/__tests__/HospitalSetupPanel.test.tsx`
- Modify: `frontend/src/__tests__/OperationsCockpit.test.tsx`
- Test: same files

- [ ] **Step 1: Run focused tests**

Run:

```bash
npm --prefix frontend test -- --runInBand src/__tests__/HospitalSetupPanel.test.tsx src/__tests__/OperationsCockpit.test.tsx
```

Expected: FAIL on stale button and heading labels.

- [ ] **Step 2: Update hospital setup assertions**

In `frontend/src/__tests__/HospitalSetupPanel.test.tsx`, replace:

```ts
    fireEvent.click(screen.getByRole('button', { name: 'Create department' }));
```

with:

```ts
    fireEvent.click(screen.getByRole('button', { name: 'Register Division' }));
```

Replace:

```ts
    expect(screen.getByText('Department created')).toBeInTheDocument();
```

with:

```ts
    expect(screen.getByText('Department created successfully.')).toBeInTheDocument();
```

Replace:

```ts
    fireEvent.click(screen.getByRole('button', { name: 'Create bed' }));
```

with:

```ts
    fireEvent.click(screen.getByRole('button', { name: 'Register Bed Node' }));
```

Replace:

```ts
    expect(screen.getByText('Bed created')).toBeInTheDocument();
```

with:

```ts
    expect(screen.getByText('Bed registered successfully.')).toBeInTheDocument();
```

- [ ] **Step 3: Update operations cockpit assertions**

In `frontend/src/__tests__/OperationsCockpit.test.tsx`, replace:

```ts
      expect(screen.getByText('Hospital Operations Cockpit')).toBeInTheDocument();
```

with:

```ts
      expect(screen.getByText('Operational Dashboard Cockpit')).toBeInTheDocument();
```

Replace:

```ts
    expect(screen.getByText('Admin command view')).toBeInTheDocument();
```

with:

```ts
    expect(screen.getByText('Admin Command Console')).toBeInTheDocument();
```

Replace:

```ts
    expect(screen.getByText('Doctor care-team view')).toBeInTheDocument();
```

with:

```ts
    expect(screen.getByText('Doctor Care-Team Interface')).toBeInTheDocument();
```

Replace:

```ts
    expect(screen.getByText('Clinician review remains required for every AI-assisted signal.')).toBeInTheDocument();
```

with:

```ts
    expect(screen.getByText(/Active clinician review and diagnostic sign-off is required/i)).toBeInTheDocument();
```

- [ ] **Step 4: Run focused tests**

Run:

```bash
npm --prefix frontend test -- --runInBand src/__tests__/HospitalSetupPanel.test.tsx src/__tests__/OperationsCockpit.test.tsx
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/__tests__/HospitalSetupPanel.test.tsx frontend/src/__tests__/OperationsCockpit.test.tsx
git commit -m "test: align operations tests with current UI copy"
```

---

### Task 9: Final Foundation Verification

**Files:**

- Verify: frontend and backend checks.

- [ ] **Step 1: Run frontend lint**

Run:

```bash
npm --prefix frontend run lint
```

Expected: PASS with no errors. A Next.js image optimization warning is acceptable only if it is still the existing warning in `frontend/src/app/(p)/patients/[id]/page.tsx`.

- [ ] **Step 2: Run frontend Jest**

Run:

```bash
npm --prefix frontend test -- --runInBand
```

Expected: PASS for all frontend test suites.

- [ ] **Step 3: Run frontend production build**

Run:

```bash
npm --prefix frontend run build
```

Expected: PASS.

- [ ] **Step 4: Run backend readiness and operations tests**

Run:

```bash
python -m pytest tests/unit/test_demo_readiness.py tests/unit/test_hospital_operations.py tests/unit/test_sync_agent_adapters.py -q
```

Expected: PASS.

- [ ] **Step 5: Run staged whitespace check**

Run:

```bash
git diff --check -- frontend backend tests docs README.md
```

Expected: PASS for files changed in this plan. If unrelated pre-existing modified files still fail, run this narrower command before committing the final verification note:

```bash
git diff --check -- frontend/jest.setup.ts frontend/src/lib/api.ts frontend/src/lib/apiErrors.ts frontend/src/lib/useTelemetry.ts frontend/src/app/login/page.tsx frontend/src/app/signup/page.tsx 'frontend/src/app/(p)/dashboard/page.tsx' 'frontend/src/app/(p)/infrastructure/page.tsx' 'frontend/src/app/(p)/patients/[id]/page.tsx' frontend/src/components/layout/TopNav.tsx frontend/src/components/system/DemoReadinessBadge.tsx frontend/src/components/system/DegradedStateBanner.tsx frontend/src/components/operations/OperationsCockpit.tsx frontend/src/components/operations/PatientDiagnosticResults.tsx frontend/src/components/operations/PatientCareTimeline.tsx frontend/src/__tests__ backend/demo_readiness.py backend/main.py tests/unit/test_demo_readiness.py
```

Expected: PASS.

- [ ] **Step 6: Commit final verification cleanup only if files changed**

If verification required small cleanup changes, commit them:

```bash
git add frontend/jest.setup.ts frontend/src/lib/api.ts frontend/src/lib/apiErrors.ts frontend/src/lib/useTelemetry.ts frontend/src/app/login/page.tsx frontend/src/app/signup/page.tsx 'frontend/src/app/(p)/dashboard/page.tsx' 'frontend/src/app/(p)/infrastructure/page.tsx' 'frontend/src/app/(p)/patients/[id]/page.tsx' frontend/src/components/layout/TopNav.tsx frontend/src/components/system/DemoReadinessBadge.tsx frontend/src/components/system/DegradedStateBanner.tsx frontend/src/components/operations/OperationsCockpit.tsx frontend/src/components/operations/PatientDiagnosticResults.tsx frontend/src/components/operations/PatientCareTimeline.tsx frontend/src/__tests__/ChatScope.test.tsx frontend/src/__tests__/ComplianceCopy.test.tsx frontend/src/__tests__/DashboardReadiness.test.tsx frontend/src/__tests__/HospitalSetupPanel.test.tsx frontend/src/__tests__/OperationsCockpit.test.tsx frontend/src/__tests__/PatientCareTimeline.test.tsx frontend/src/__tests__/PatientDiagnosticResults.test.tsx frontend/src/__tests__/TopNav.test.tsx backend/demo_readiness.py backend/main.py tests/unit/test_demo_readiness.py
git commit -m "chore: verify clinic command center foundation"
```

Expected: commit only if verification produced additional edits.

---

## Completion Criteria

This foundation plan is complete when:

- `/demo-readiness` returns PHI-safe readiness status.
- Dashboard shows readiness and clean degraded states.
- Unsupported frontend compliance, encryption, uptime, and accuracy claims are removed.
- Patient-facing diagnostic results include clinician consultation safety language.
- Frontend Jest passes.
- Frontend build passes.
- Focused backend tests pass.
- Changed files pass whitespace checks.

After completion, write the next plan for the clinic visit workspace.
