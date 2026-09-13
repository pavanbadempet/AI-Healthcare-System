import { describe, it, expect, beforeAll, afterAll } from 'bun:test';
import { createApp } from '../src/index';
import { isRateLimitExempt } from '../src/middleware/rate_limiter';
import { isApiOrSpecialRoute } from '../src/static';

describe('Dual-Core Aggregate Health Checker (/healthz/aggregate)', () => {
  let mockRustServer: any;
  let mockPythonServer: any;
  let hangingServer: any;

  const mockRustPort = 8821;
  const mockPythonPort = 8822;
  const hangingPort = 8823;
  let app: any;

  beforeAll(() => {
    // Healthy Rust Systems Core mock
    mockRustServer = Bun.serve({
      port: mockRustPort,
      hostname: '127.0.0.1',
      fetch(req) {
        const url = new URL(req.url);
        if (url.pathname === '/healthz') {
          return new Response(
            JSON.stringify({
              status: 'ok',
              gateway: 'Rust Axum / Tokio PID 1 Native Engine',
              threads: 16,
            }),
            { headers: { 'Content-Type': 'application/json' } }
          );
        }
        return new Response('Not Found', { status: 404 });
      },
    });

    // Healthy Python Deliberation Core mock
    mockPythonServer = Bun.serve({
      port: mockPythonPort,
      hostname: '127.0.0.1',
      fetch(req) {
        const url = new URL(req.url);
        if (url.pathname === '/healthz') {
          return new Response(
            JSON.stringify({
              status: 'healthy',
              service: 'AI Healthcare System Brain',
              models_loaded: ['qrs_detector', 'risk_scorer'],
            }),
            { headers: { 'Content-Type': 'application/json' } }
          );
        }
        return new Response('Not Found', { status: 404 });
      },
    });

    // Hanging mock server to test timeout resilience
    hangingServer = Bun.serve({
      port: hangingPort,
      hostname: '127.0.0.1',
      async fetch() {
        // Sleep for 2.5 seconds to trigger probe timeout
        await new Promise((resolve) => setTimeout(resolve, 2500));
        return new Response(JSON.stringify({ status: 'late' }), {
          headers: { 'Content-Type': 'application/json' },
        });
      },
    });

    app = createApp({
      configOverride: {
        rustBackendUrl: `http://127.0.0.1:${mockRustPort}`,
        pythonBackendUrl: `http://127.0.0.1:${mockPythonPort}`,
        staticDir: 'non_existent_dir_for_test',
      },
    });
  });

  afterAll(() => {
    if (mockRustServer) mockRustServer.stop();
    if (mockPythonServer) mockPythonServer.stop();
    if (hangingServer) hangingServer.stop();
  });

  describe('Healthy Dual-Core State (200 OK)', () => {
    it('concurrently checks Rust and Python cores and aggregates vitals', async () => {
      const res = await app.handle(new Request('http://127.0.0.1:8000/healthz/aggregate'));
      expect(res.status).toBe(200);

      const data: any = await res.json();
      expect(data.status).toBe('ok');
      expect(data.timestamp).toBeTruthy();
      expect(typeof data.aggregate_latency_ms).toBe('number');
      expect(data.aggregate_latency_ms).toBeGreaterThanOrEqual(0);

      // Edge runtime vitals
      expect(data.edge.status).toBe('ok');
      expect(data.edge.runtime).toBe('bun');
      expect(data.edge.version).toBe(Bun.version);
      expect(data.edge.uptime_seconds).toBeGreaterThanOrEqual(0);
      expect(data.edge.memory_mb).toBeGreaterThan(0);

      // Rust Systems Core verification
      expect(data.rust_core.status).toBe('ok');
      expect(data.rust_core.latency_ms).toBeGreaterThanOrEqual(0);
      expect(data.rust_core.url).toContain(`:${mockRustPort}/healthz`);
      expect(data.rust_core.details.gateway).toBe('Rust Axum / Tokio PID 1 Native Engine');
      expect(data.rust_core.error).toBeNull();

      // Python Deliberation Core verification
      expect(data.python_core.status).toBe('ok');
      expect(data.python_core.latency_ms).toBeGreaterThanOrEqual(0);
      expect(data.python_core.url).toContain(`:${mockPythonPort}/healthz`);
      expect(data.python_core.details.service).toBe('AI Healthcare System Brain');
      expect(data.python_core.error).toBeNull();

      // Dual service mapping compatibility
      expect(data.services.rust_systems_core.status).toBe('ok');
      expect(data.services.python_deliberation_core.status).toBe('ok');
    });
  });

  describe('Degraded & Unhealthy States', () => {
    it('handles Python core offline with strict 503 degraded response', async () => {
      const offlinePythonApp = createApp({
        configOverride: {
          rustBackendUrl: `http://127.0.0.1:${mockRustPort}`,
          pythonBackendUrl: 'http://127.0.0.1:59991', // Offline port
        },
      });

      const res = await offlinePythonApp.handle(
        new Request('http://127.0.0.1:8000/healthz/aggregate?strict=true')
      );
      expect(res.status).toBe(503);

      const data: any = await res.json();
      expect(data.status).toBe('degraded');
      expect(data.rust_core.status).toBe('ok');
      expect(data.python_core.status).toBe('unreachable');
      expect(data.python_core.error).toBeTruthy();
    });

    it('handles Rust core offline with 503 degraded response', async () => {
      const offlineRustApp = createApp({
        configOverride: {
          rustBackendUrl: 'http://127.0.0.1:59992', // Offline port
          pythonBackendUrl: `http://127.0.0.1:${mockPythonPort}`,
        },
      });

      const res = await offlineRustApp.handle(
        new Request('http://127.0.0.1:8000/healthz/aggregate')
      );
      expect(res.status).toBe(503);

      const data: any = await res.json();
      expect(data.status).toBe('degraded');
      expect(data.rust_core.status).toBe('unreachable');
      expect(data.rust_core.error).toBeTruthy();
      expect(data.python_core.status).toBe('ok');
    });

    it('handles both upstream cores offline with 503 unhealthy response', async () => {
      const bothOfflineApp = createApp({
        configOverride: {
          rustBackendUrl: 'http://127.0.0.1:59993',
          pythonBackendUrl: 'http://127.0.0.1:59994',
        },
      });

      const res = await bothOfflineApp.handle(
        new Request('http://127.0.0.1:8000/healthz/aggregate')
      );
      expect(res.status).toBe(503);

      const data: any = await res.json();
      expect(data.status).toBe('unhealthy');
      expect(data.rust_core.status).toBe('unreachable');
      expect(data.python_core.status).toBe('unreachable');
      expect(data.edge.status).toBe('ok'); // Edge remains alive
    });

    it('reports degraded status when upstream core returns HTTP 500 error', async () => {
      const errorServer = Bun.serve({
        port: 8824,
        hostname: '127.0.0.1',
        fetch() {
          return new Response(JSON.stringify({ error: 'Internal Database Failure' }), {
            status: 500,
            headers: { 'Content-Type': 'application/json' },
          });
        },
      });

      try {
        const errorApp = createApp({
          configOverride: {
            rustBackendUrl: 'http://127.0.0.1:8824',
            pythonBackendUrl: `http://127.0.0.1:${mockPythonPort}`,
          },
        });

        const res = await errorApp.handle(new Request('http://127.0.0.1:8000/healthz/aggregate'));
        expect(res.status).toBe(503);

        const data: any = await res.json();
        expect(data.status).toBe('degraded');
        expect(data.rust_core.status).toBe('degraded');
        expect(data.rust_core.error).toContain('500');
      } finally {
        errorServer.stop();
      }
    });

    it('aborts cleanly and marks unreachable on probe timeout without hanging edge', async () => {
      const timeoutApp = createApp({
        configOverride: {
          rustBackendUrl: `http://127.0.0.1:${mockRustPort}`,
          pythonBackendUrl: `http://127.0.0.1:${hangingPort}`,
        },
      });

      const startTime = performance.now();
      const res = await timeoutApp.handle(
        new Request('http://127.0.0.1:8000/healthz/aggregate?strict=true')
      );
      const elapsedMs = performance.now() - startTime;

      expect(res.status).toBe(503);
      const data: any = await res.json();
      expect(data.status).toBe('degraded');
      expect(data.python_core.status).toBe('unreachable');
      expect(data.python_core.error).toContain('timed out');
      expect(elapsedMs).toBeLessThan(2000); // Must timeout cleanly before 2000ms
    });
  });

  describe('Rate Limiter & SPA Fallback Exemption', () => {
    it('exempts /healthz/aggregate from client rate limiting', () => {
      expect(isRateLimitExempt('/healthz/aggregate')).toBe(true);
      expect(isRateLimitExempt('/healthz')).toBe(true);
      expect(isRateLimitExempt('/healthz/live')).toBe(true);
    });

    it('does not throttle high-frequency aggregate health polling', async () => {
      const promises = Array.from({ length: 25 }, () =>
        app.handle(new Request('http://127.0.0.1:8000/healthz/aggregate'))
      );
      const responses = await Promise.all(promises);

      for (const res of responses) {
        expect(res.status).toBe(200);
      }
    });

    it('exempts /healthz/aggregate from static SPA fallback', async () => {
      expect(isApiOrSpecialRoute('/healthz/aggregate')).toBe(true);

      const res = await app.handle(new Request('http://127.0.0.1:8000/healthz/aggregate'));
      expect(res.status).toBe(200);
      const data: any = await res.json();
      expect(data.edge.runtime).toBe('bun');
      expect(data.status).toBe('ok');
    });
  });
});
