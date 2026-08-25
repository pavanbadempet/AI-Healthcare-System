## 2026-08-21T05:55:45Z

### Milestone 4: Bun ElysiaJS API Orchestration Layer (BFF Gateway & Proxy - Worker 2)
**Working Directory**: c:\Users\pavan\OneDrive\Documents\GitHub\AI-Healthcare-System\.agents\sub_orch_m4_2
**Original Request**: c:\Users\pavan\OneDrive\Documents\GitHub\AI-Healthcare-System\.agents\ORIGINAL_REQUEST.md
**Project Spec**: c:\Users\pavan\OneDrive\Documents\GitHub\AI-Healthcare-System\PROJECT.md
**Routes Specification**: c:\Users\pavan\OneDrive\Documents\GitHub\AI-Healthcare-System\.agents\explorer_survey_routes_1\routes_survey.md

**Objective**:
Create a high-performance Bun-powered ElysiaJS server in `edge_gateway/` that sits as the edge entry point (PID 1 in container / production), handling request routing, transparent proxying to Rust backend (`http://127.0.0.1:8001`), CORS, compression, rate limiting, JWT verification, WebSocket & SSE proxying, health aggregation, and static asset serving for the Vite React 19 frontend SPA.

**Instructions**:
1. Read `ORIGINAL_REQUEST.md`, `PROJECT.md`, and `routes_survey.md`.
2. Create `edge_gateway/`:
   - `package.json`: Dependencies: `elysia`, `@elysiajs/cors`, `@elysiajs/jwt`, `@elysiajs/static`.
   - `tsconfig.json`: Standard TypeScript configuration for Bun.
   - `src/index.ts`: Main Elysia server listening on port 8000 (or `PORT` env var).
   - `src/proxy.ts`: High-speed reverse proxy forwarding HTTP requests, headers (`X-Forwarded-For`, `X-Real-IP`, `X-Request-ID`), and SSE streaming (`POST /v1/chat/stream`) to Rust backend (`http://127.0.0.1:8001`).
   - `src/ws_proxy.ts`: Transparent WebSocket proxying for `/v1/telemetry/stream` and `/v1/telemetry/vitals/:id` forwarding to `ws://127.0.0.1:8001`.
   - `src/middleware/`: CORS configuration, JWT verification middleware, rate limiting (100 req/min per IP with burst allowance), response compression.
   - `src/static.ts`: Static file server serving `frontend/dist/` assets with SPA HTML fallback routing.
3. Test locally using `bun install` and `bun test` or test verification script.
4. Verify that edge proxy adds <5ms overhead per proxied request.
5. Write `handoff.md` and notify parent orchestrator when complete.
