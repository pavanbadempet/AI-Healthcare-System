/**
 * Bun + ElysiaJS Edge Gateway & API Orchestration Layer
 * Entry Point (PID 1) for AI Healthcare System Full-Stack Architecture
 */

import { Elysia } from 'elysia';
import { config, EdgeConfig } from './config';
import { requestContext } from './middleware/request_context';
import { createCorsMiddleware } from './middleware/cors';
import { rateLimitMiddleware } from './middleware/rate_limiter';
import { jwtMiddleware } from './middleware/jwt';
import { createHealthPlugin } from './health';
import { createProxyPlugin } from './proxy';
import { createWsProxyPlugin } from './ws_proxy';
import { createStaticSpaPlugin } from './static';

export interface AppOptions {
  configOverride?: Partial<EdgeConfig>;
}

export function createApp(options: AppOptions = {}) {
  const cfg = { ...config, ...options.configOverride };

  const app = new Elysia({ name: 'ai-healthcare-edge-gateway' })
    // Global request telemetry & context
    .use(requestContext)
    // CORS policy
    .use(createCorsMiddleware())
    // Rate limiter
    .use(rateLimitMiddleware)
    // JWT verification
    .use(jwtMiddleware)
    // Health & readiness probes
    .use(createHealthPlugin(cfg.rustBackendUrl))
    // WebSocket streaming proxy
    .use(createWsProxyPlugin(cfg.rustWsUrl))
    // HTTP API reverse proxy to Rust backend
    .use(createProxyPlugin({ targetBaseUrl: cfg.rustBackendUrl }))
    // Static asset server & SPA fallback for Vite React 19 frontend
    .use(createStaticSpaPlugin(cfg.staticDir));

  return app;
}

export const app = createApp();

// Start the server if executed directly
if (import.meta.main) {
  const port = config.port;
  const host = config.host;

  console.log(`=======================================================`);
  console.log(`  AI Healthcare System - Bun ElysiaJS Edge Gateway   `);
  console.log(`=======================================================`);
  console.log(`  🚀 Edge Gateway Listening: http://${host}:${port}`);
  console.log(`  🔗 Upstream Rust Backend:  ${config.rustBackendUrl}`);
  console.log(`  ⚡ Upstream WebSocket:     ${config.rustWsUrl}`);
  console.log(`  📁 Static SPA Assets Dir:  ${config.staticDir}`);
  console.log(`  🛡️ Rate Limiting:         ${config.rateLimitPerMinute} req/min`);
  console.log(`=======================================================`);

  app.listen({ port, hostname: host }, () => {
    console.log(`[EDGE GATEWAY] Server running on port ${port}`);
  });

  // Graceful shutdown handling
  const shutdown = () => {
    console.log('\n[EDGE GATEWAY] Gracefully stopping edge gateway...');
    app.stop();
    process.exit(0);
  };

  process.on('SIGINT', shutdown);
  process.on('SIGTERM', shutdown);
}
