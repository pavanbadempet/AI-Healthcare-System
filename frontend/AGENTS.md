<!-- BEGIN:vite-agent-rules -->
# Frontend Rules

This frontend is a client-side React SPA powered by Vite 6, Tailwind CSS v4, and React Router DOM. 

## Before Editing

- Read root `../AGENTS.md` first.
- Components are client-side only. Do not add Next.js Server Components, server actions, or Next-specific routing APIs.

## Structure

- App entry and main router configuration live in [App.tsx](file:///c:/Users/pavan/OneDrive/Documents/GitHub/AI-Healthcare-System/frontend/src/App.tsx).
- Page components live in [src/pages/](file:///c:/Users/pavan/OneDrive/Documents/GitHub/AI-Healthcare-System/frontend/src/pages/) and are lazy-loaded via `React.lazy()` inside `App.tsx`.
- Shared UI components live in `frontend/src/components/`.
- Frontend libraries, state managers (Zustand), and hooks live in `frontend/src/lib/`.
- Public static assets live in `frontend/public/`.
- Vitest unit tests live in `frontend/src/__tests__/`.
- Playwright E2E tests live in `frontend/tests/`.

## Rules

- Use `VITE_PUBLIC_API_URL` or fallback to `http://127.0.0.1:8000` for API connection.
- Prediction, AI chat, report-analysis, and other patient-facing medical AI views must show a medical disclaimer and recommend consulting a qualified clinician for diagnosis, treatment, or emergencies.
- Do not put patient names, DOBs, health records, or other PII into tests, fixtures, logs, screenshots, or snapshots.
- Keep API helpers in `frontend/src/lib/api.ts`; do not scatter raw backend URL construction through pages/components.
- Prefer `npm --prefix frontend run dev` for local dev (serves at `http://127.0.0.1:3000`).

## Checks

```bash
# Linting
npm --prefix frontend run lint

# Vitest Unit Tests
npm --prefix frontend run test

# Production Build
npm --prefix frontend run build
```
<!-- END:vite-agent-rules -->
