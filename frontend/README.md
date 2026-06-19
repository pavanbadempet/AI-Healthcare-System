# AI Healthcare Frontend

Next.js 16 App Router frontend for the AI Healthcare System.

## Requirements

- Node.js 20.9+
- Backend available at `http://127.0.0.1:8000` unless `NEXT_PUBLIC_API_URL` is set

## Development

```bash
npm install
npm run dev -- -H 127.0.0.1 -p 3000
```

Open `http://127.0.0.1:3000`.

## Structure

- `src/app/` - App Router routes and layouts
- `src/components/` - shared UI components
- `src/lib/` - API helpers, auth, hooks, and frontend utilities
- `src/__tests__/` - Jest unit/component tests
- `tests/` - Playwright visual/browser tests
- `public/` - public assets

## Checks

```bash
npm run lint
npm test
npm exec playwright test
```

Prediction, AI chat, report-analysis, and other patient-facing medical AI views must display the required medical disclaimer.
