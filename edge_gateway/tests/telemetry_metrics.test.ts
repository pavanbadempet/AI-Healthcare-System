import { describe, it, expect, beforeAll, afterAll, beforeEach } from 'bun:test';
import { createApp } from '../src/index';
import { telemetryCollector, HISTOGRAM_BUCKETS } from '../src/health';
import { isRateLimitExempt } from '../src/middleware/rate_limiter';
import { isApiOrSpecialRoute } from '../src/static';

describe('Prometheus Telemetry & Metrics Exporter (/metrics/prometheus)', () => {
  let mockRustBackend: any;
  let mockPythonBackend: any;
  const mockRustPort = 8815;
  const mockPythonPort = 8816;
  let app: any;

  beforeAll(() => {
    mockRustBackend = Bun.serve({
      port: mockRustPort,
      hostname: '127.0.0.1',
      fetch(req) {
        const url = new URL(req.url);
        if (url.pathname === '/healthz') {
          return new Response(JSON.stringify({ status: 'ok', engine: 'rust-axum' }), {
            headers: { 'Content-Type': 'application/json' },
          });
        }
        if (url.pathname.startsWith('/api/')) {
          return new Response(JSON.stringify({ data: 'rust_response' }), {
            headers: { 'Content-Type': 'application/json' },
          });
        }
        return new Response('Not Found', { status: 404 });
      },
    });

    mockPythonBackend = Bun.serve({
      port: mockPythonPort,
      hostname: '127.0.0.1',
      fetch(req) {
        const url = new URL(req.url);
        if (url.pathname === '/healthz') {
          return new Response(JSON.stringify({ status: 'healthy', service: 'python-deliberation-core' }), {
            headers: { 'Content-Type': 'application/json' },
          });
        }
        if (url.pathname.startsWith('/v1/clinical-agents')) {
          return new Response(JSON.stringify({ thought_chain: ['analyzed', 'deliberated'] }), {
            headers: { 'Content-Type': 'application/json' },
          });
        }
        return new Response('Not Found', { status: 404 });
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
    if (mockRustBackend) mockRustBackend.stop();
    if (mockPythonBackend) mockPythonBackend.stop();
  });

  beforeEach(() => {
    telemetryCollector.reset();
  });

  describe('TelemetryCollector Unit Logic', () => {
    it('returns zero quantiles and empty counts on cold start', () => {
      const q = telemetryCollector.getQuantiles();
      expect(q.count).toBe(0);
      expect(q.sum).toBe(0);
      expect(q.p50).toBe(0);
      expect(q.p95).toBe(0);
      expect(q.p99).toBe(0);

      const upstreams = telemetryCollector.getUpstreamCounts();
      expect(upstreams.rust_backend).toBe(0);
      expect(upstreams.python_brain).toBe(0);
      expect(upstreams.edge_gateway).toBe(0);
    });

    it('calculates real-time p50, p95, and p99 quantiles accurately', () => {
      // Record 100 requests from 1ms (0.001s) to 100ms (0.100s)
      for (let i = 1; i <= 100; i++) {
        const durationSec = i / 1000.0;
        telemetryCollector.recordRequest('rust_backend', durationSec);
      }

      const q = telemetryCollector.getQuantiles();
      expect(q.count).toBe(100);
      expect(q.sum).toBeCloseTo(5.05, 2);

      // p50 is index 50 -> ~0.051s
      expect(q.p50).toBeGreaterThanOrEqual(0.045);
      expect(q.p50).toBeLessThanOrEqual(0.055);

      // p95 is index 95 -> ~0.096s
      expect(q.p95).toBeGreaterThanOrEqual(0.090);
      expect(q.p95).toBeLessThanOrEqual(0.100);

      // p99 is index 99 -> ~0.100s
      expect(q.p99).toBeGreaterThanOrEqual(0.098);
      expect(q.p99).toBeLessThanOrEqual(0.100);
    });

    it('tracks upstream distribution counters correctly across targets', () => {
      telemetryCollector.recordRequest('rust_backend', 0.002);
      telemetryCollector.recordRequest('rust_backend', 0.004);
      telemetryCollector.recordRequest('python_brain', 0.050);
      telemetryCollector.recordRequest('edge_gateway', 0.0005);
      telemetryCollector.recordRequest('edge_gateway', 0.0008);
      telemetryCollector.recordRequest('edge_gateway', 0.0012);

      const counts = telemetryCollector.getUpstreamCounts();
      expect(counts.rust_backend).toBe(2);
      expect(counts.python_brain).toBe(1);
      expect(counts.edge_gateway).toBe(3);
    });

    it('formats Prometheus text with histograms, gauges, and counters', () => {
      telemetryCollector.recordRequest('rust_backend', 0.0015);
      telemetryCollector.recordRequest('python_brain', 0.020);

      const text = telemetryCollector.toPrometheusText();

      // Histogram headers
      expect(text).toContain('# HELP edge_request_duration_seconds Real-time HTTP request latency in seconds');
      expect(text).toContain('# TYPE edge_request_duration_seconds histogram');

      // Granular buckets
      for (const bucket of HISTOGRAM_BUCKETS) {
        expect(text).toContain(`edge_request_duration_seconds_bucket{le="${bucket.toFixed(3)}"}`);
      }
      expect(text).toContain('edge_request_duration_seconds_bucket{le="+Inf"} 2');
      expect(text).toContain('edge_request_duration_seconds_count 2');

      // Quantile gauges
      expect(text).toContain('# HELP edge_request_latency_p50_seconds');
      expect(text).toContain('# TYPE edge_request_latency_p50_seconds gauge');
      expect(text).toContain('# HELP edge_request_latency_p95_seconds');
      expect(text).toContain('# TYPE edge_request_latency_p95_seconds gauge');
      expect(text).toContain('# HELP edge_request_latency_p99_seconds');
      expect(text).toContain('# TYPE edge_request_latency_p99_seconds gauge');

      // Upstream counters
      expect(text).toContain('# HELP edge_upstream_requests_total');
      expect(text).toContain('# TYPE edge_upstream_requests_total counter');
      expect(text).toContain('edge_upstream_requests_total{upstream="rust_backend"} 1');
      expect(text).toContain('edge_upstream_requests_total{upstream="python_brain"} 1');
      expect(text).toContain('edge_upstream_requests_total{upstream="edge_gateway"} 0');
    });
  });

  describe('HTTP Integration via /metrics/prometheus', () => {
    it('serves /metrics/prometheus with correct content-type and 200 OK', async () => {
      const res = await app.handle(new Request('http://127.0.0.1:8000/metrics/prometheus'));
      expect(res.status).toBe(200);
      expect(res.headers.get('content-type')).toContain('text/plain');
      expect(res.headers.get('content-type')).toContain('version=0.0.4');

      const body = await res.text();
      expect(body).toContain('edge_request_duration_seconds');
      expect(body).toContain('edge_upstream_requests_total');
    });

    it('automatically records live traffic into telemetry metrics', async () => {
      // 1. Send request to Edge Gateway route
      await app.handle(new Request('http://127.0.0.1:8000/healthz/live'));

      // 2. Send request to Rust backend proxy route
      await app.handle(new Request('http://127.0.0.1:8000/api/patients'));

      // 3. Send request to Python brain proxy route
      await app.handle(new Request('http://127.0.0.1:8000/v1/clinical-agents'));

      // Allow microtask queue and onAfterResponse hooks to settle
      for (let i = 0; i < 30; i++) {
        if (telemetryCollector.getUpstreamCounts().python_brain > 0) break;
        await new Promise((r) => setTimeout(r, 10));
      }

      // 4. Fetch Prometheus metrics
      const res = await app.handle(new Request('http://127.0.0.1:8000/metrics/prometheus'));
      expect(res.status).toBe(200);
      const body = await res.text();

      // Verify upstream distribution counters incremented
      expect(body).toMatch(/edge_upstream_requests_total\{upstream="rust_backend"\} [1-9]\d*/);
      expect(body).toMatch(/edge_upstream_requests_total\{upstream="python_brain"\} [1-9]\d*/);
      expect(body).toMatch(/edge_upstream_requests_total\{upstream="edge_gateway"\} [1-9]\d*/);
    });
  });

  describe('Rate Limiter & SPA Fallback Exemption', () => {
    it('exempts /metrics/prometheus from rate limiting', () => {
      expect(isRateLimitExempt('/metrics/prometheus')).toBe(true);
      expect(isRateLimitExempt('/metrics')).toBe(true);
      expect(isRateLimitExempt('/metrics/prometheus/subpath')).toBe(true);
    });

    it('does not throttle high-frequency Prometheus scraping requests', async () => {
      // Burst 30 requests rapidly
      const promises = Array.from({ length: 30 }, () =>
        app.handle(new Request('http://127.0.0.1:8000/metrics/prometheus'))
      );
      const responses = await Promise.all(promises);

      for (const res of responses) {
        expect(res.status).toBe(200);
      }
    });

    it('exempts /metrics/prometheus from static SPA fallback', async () => {
      expect(isApiOrSpecialRoute('/metrics/prometheus')).toBe(true);
      expect(isApiOrSpecialRoute('/metrics')).toBe(true);

      const res = await app.handle(new Request('http://127.0.0.1:8000/metrics/prometheus'));
      expect(res.status).toBe(200);
      const text = await res.text();
      // Must NOT be HTML SPA fallback
      expect(text).not.toContain('<!DOCTYPE html>');
      expect(text).toContain('# HELP edge_request_duration_seconds');
    });
  });
});
