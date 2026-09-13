import { Elysia } from 'elysia';
import { config } from './config';
import { metricsRegistry } from './metrics';

export interface BackendHealthProbe {
  status: 'ok' | 'degraded' | 'unreachable';
  latency_ms: number;
  latencyMs: number;
  url: string;
  details?: any;
  error?: string | null;
}

export const HISTOGRAM_BUCKETS = [
  0.001, 0.002, 0.005, 0.010, 0.025, 0.050, 0.100, 0.250, 0.500, 1.000, 2.500, 5.000,
];

export class TelemetryCollector {
  private latencies: number[] = [];
  private maxSamples = 5000;
  private totalCount = 0;
  private totalSum = 0;
  private upstreamCounts: Record<'rust_backend' | 'python_brain' | 'edge_gateway', number> = {
    rust_backend: 0,
    python_brain: 0,
    edge_gateway: 0,
  };

  public recordRequest(
    upstream: 'rust_backend' | 'python_brain' | 'edge_gateway',
    durationSec: number
  ): void {
    this.upstreamCounts[upstream] = (this.upstreamCounts[upstream] || 0) + 1;
    this.latencies.push(durationSec);
    this.totalSum += durationSec;
    this.totalCount++;
    if (this.latencies.length > this.maxSamples) {
      this.latencies.shift();
    }
  }

  public getQuantiles(): { p50: number; p95: number; p99: number; count: number; sum: number } {
    if (this.latencies.length === 0) {
      return { p50: 0, p95: 0, p99: 0, count: 0, sum: 0 };
    }
    const sorted = [...this.latencies].sort((a, b) => a - b);
    const n = sorted.length;
    const p50 = sorted[Math.min(Math.floor(n * 0.50), n - 1)];
    const p95 = sorted[Math.min(Math.floor(n * 0.95), n - 1)];
    const p99 = sorted[Math.min(Math.floor(n * 0.99), n - 1)];
    return {
      p50: parseFloat(p50.toFixed(6)),
      p95: parseFloat(p95.toFixed(6)),
      p99: parseFloat(p99.toFixed(6)),
      count: this.totalCount,
      sum: parseFloat(this.totalSum.toFixed(6)),
    };
  }

  public getUpstreamCounts(): Record<'rust_backend' | 'python_brain' | 'edge_gateway', number> {
    return { ...this.upstreamCounts };
  }

  public reset(): void {
    this.latencies = [];
    this.totalCount = 0;
    this.totalSum = 0;
    this.upstreamCounts = {
      rust_backend: 0,
      python_brain: 0,
      edge_gateway: 0,
    };
  }

  public toPrometheusText(): string {
    const lines: string[] = [];
    const q = this.getQuantiles();

    // 1. edge_request_duration_seconds histogram
    lines.push('# HELP edge_request_duration_seconds Real-time HTTP request latency in seconds');
    lines.push('# TYPE edge_request_duration_seconds histogram');
    for (const le of HISTOGRAM_BUCKETS) {
      const bucketCount = this.latencies.filter((lat) => lat <= le).length;
      lines.push(`edge_request_duration_seconds_bucket{le="${le.toFixed(3)}"} ${bucketCount}`);
    }
    lines.push(`edge_request_duration_seconds_bucket{le="+Inf"} ${this.totalCount}`);
    lines.push(`edge_request_duration_seconds_sum ${q.sum}`);
    lines.push(`edge_request_duration_seconds_count ${this.totalCount}`);
    lines.push('');

    // 2. Real-time quantiles gauges
    lines.push('# HELP edge_request_latency_p50_seconds Real-time 50th percentile (median) request latency');
    lines.push('# TYPE edge_request_latency_p50_seconds gauge');
    lines.push(`edge_request_latency_p50_seconds ${q.p50}`);
    lines.push('');

    lines.push('# HELP edge_request_latency_p95_seconds Real-time 95th percentile request latency');
    lines.push('# TYPE edge_request_latency_p95_seconds gauge');
    lines.push(`edge_request_latency_p95_seconds ${q.p95}`);
    lines.push('');

    lines.push('# HELP edge_request_latency_p99_seconds Real-time 99th percentile request latency');
    lines.push('# TYPE edge_request_latency_p99_seconds gauge');
    lines.push(`edge_request_latency_p99_seconds ${q.p99}`);
    lines.push('');

    // 3. Upstream routing distribution counters
    lines.push('# HELP edge_upstream_requests_total Total HTTP requests dispatched to upstream targets');
    lines.push('# TYPE edge_upstream_requests_total counter');
    lines.push(`edge_upstream_requests_total{upstream="rust_backend"} ${this.upstreamCounts.rust_backend}`);
    lines.push(`edge_upstream_requests_total{upstream="python_brain"} ${this.upstreamCounts.python_brain}`);
    lines.push(`edge_upstream_requests_total{upstream="edge_gateway"} ${this.upstreamCounts.edge_gateway}`);
    lines.push('');

    // 4. Also append metricsRegistry metrics for backwards compatibility
    lines.push(metricsRegistry.toPrometheusText());

    return lines.join('\n');
  }
}

export const telemetryCollector = new TelemetryCollector();

export async function probeBackend(targetUrl: string, path: string = '/healthz', timeoutMs: number = 1000): Promise<BackendHealthProbe> {
  const probeUrl = `${targetUrl}${path}`;
  const startTime = performance.now();

  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

    const response = await fetch(probeUrl, {
      method: 'GET',
      headers: { 'Accept': 'application/json', 'User-Agent': 'Bun-Elysia-Edge-Health/1.0' },
      signal: controller.signal,
    });
    clearTimeout(timeoutId);

    const latencyMs = parseFloat((performance.now() - startTime).toFixed(2));

    if (response.ok) {
      let data = null;
      try {
        data = await response.json();
      } catch (_) {}

      return {
        status: 'ok',
        latency_ms: latencyMs,
        latencyMs,
        url: probeUrl,
        details: data || { status: 'ok' },
        error: null,
      };
    } else {
      return {
        status: 'degraded',
        latency_ms: latencyMs,
        latencyMs,
        url: probeUrl,
        error: `HTTP ${response.status} ${response.statusText}`,
      };
    }
  } catch (error: any) {
    const latencyMs = parseFloat((performance.now() - startTime).toFixed(2));
    return {
      status: 'unreachable',
      latency_ms: latencyMs,
      latencyMs,
      url: probeUrl,
      error: error.name === 'AbortError' ? 'Probe timed out' : error.message || 'Connection refused',
    };
  }
}

export function probeRustBackend(targetUrl: string = config.rustBackendUrl, timeoutMs: number = 1000): Promise<BackendHealthProbe> {
  return probeBackend(targetUrl, '/healthz', timeoutMs);
}

export function createHealthPlugin(
  rustBackendUrl: string = config.rustBackendUrl,
  pythonBackendUrl: string = config.pythonBackendUrl
) {
  return new Elysia({ name: 'plugin:health-aggregator' })
    .derive({ as: 'global' }, () => ({
      edgeReqStartTime: performance.now(),
    }))
    .onAfterResponse({ as: 'global' }, ({ request, set, edgeReqStartTime }) => {
      const durationSec = (performance.now() - (edgeReqStartTime || performance.now())) / 1000.0;
      const url = new URL(request.url);
      const pathname = url.pathname;
      let upstream: 'rust_backend' | 'python_brain' | 'edge_gateway' = 'rust_backend';
      if (
        pathname.startsWith('/v1/agentic') ||
        pathname.startsWith('/v1/clinical-agents') ||
        pathname.startsWith('/v1/ai')
      ) {
        upstream = 'python_brain';
      } else if (
        pathname.startsWith('/health') ||
        pathname.startsWith('/healthz') ||
        pathname.startsWith('/metrics') ||
        pathname.startsWith('/assets') ||
        pathname === '/' ||
        pathname === '/favicon.ico'
      ) {
        upstream = 'edge_gateway';
      } else {
        upstream = 'rust_backend';
      }
      telemetryCollector.recordRequest(upstream, durationSec);
    })
    .get('/healthz/live', () => ({
      status: 'alive',
      timestamp: new Date().toISOString(),
    }))
    .get('/healthz/ready', async ({ set }) => {
      const backend = await probeRustBackend(rustBackendUrl);
      const isReady = backend.status === 'ok';
      if (!isReady) {
        set.status = 503;
      }
      return {
        status: isReady ? 'ready' : 'not_ready',
        edge: { status: 'ok' },
        backend,
        timestamp: new Date().toISOString(),
      };
    })
    .get('/health', async () => {
      const mem = process.memoryUsage();
      const backend = await probeRustBackend(rustBackendUrl);

      const isOverallHealthy = backend.status === 'ok';

      return {
        status: isOverallHealthy ? 'healthy' : 'degraded',
        timestamp: new Date().toISOString(),
        edge: {
          status: 'ok',
          runtime: 'bun',
          version: Bun.version,
          uptime_seconds: Math.floor(process.uptime()),
          memory: {
            rss_mb: +(mem.rss / (1024 * 1024)).toFixed(2),
            heap_used_mb: +(mem.heapUsed / (1024 * 1024)).toFixed(2),
            heap_total_mb: +(mem.heapTotal / (1024 * 1024)).toFixed(2),
          },
        },
        backend,
      };
    })
    .get('/healthz', async () => {
      const mem = process.memoryUsage();
      const backend = await probeRustBackend(rustBackendUrl);

      return {
        status: backend.status === 'ok' ? 'ok' : 'degraded',
        edge_status: 'ok',
        backend_status: backend.status,
        timestamp: new Date().toISOString(),
        uptime_seconds: Math.floor(process.uptime()),
        memory_mb: +(mem.rss / (1024 * 1024)).toFixed(2),
        backend,
      };
    })
    .get('/healthz/aggregate', async ({ request, set }) => {
      const aggStart = performance.now();
      const [rustProbe, pythonProbe] = await Promise.all([
        probeBackend(rustBackendUrl, '/healthz', 1000),
        probeBackend(pythonBackendUrl, '/healthz', 1000),
      ]);
      const aggregateLatencyMs = parseFloat((performance.now() - aggStart).toFixed(2));

      const mem = process.memoryUsage();
      const isRustOk = rustProbe.status === 'ok';
      const isPythonOk = pythonProbe.status === 'ok';

      const url = new URL(request.url);
      const isStrict = url.searchParams.get('strict') === 'true' || request.headers.get('x-health-strict') === 'true';

      let status: 'ok' | 'degraded' | 'unhealthy' = 'ok';
      if (isRustOk && isPythonOk) {
        status = 'ok';
      } else if (isRustOk && !isPythonOk) {
        status = isStrict ? 'degraded' : 'ok';
        if (isStrict) set.status = 503;
      } else if (!isRustOk && isPythonOk) {
        status = 'degraded';
        set.status = 503;
      } else {
        status = 'unhealthy';
        set.status = 503;
      }

      return {
        status,
        timestamp: new Date().toISOString(),
        aggregate_latency_ms: aggregateLatencyMs,
        edge: {
          status: 'ok',
          runtime: 'bun',
          version: Bun.version,
          uptime_seconds: Math.floor(process.uptime()),
          memory_mb: +(mem.rss / (1024 * 1024)).toFixed(2),
        },
        rust_core: rustProbe,
        python_core: pythonProbe,
        services: {
          rust_systems_core: rustProbe,
          python_deliberation_core: pythonProbe,
        },
      };
    })
    .get('/metrics/prometheus', ({ set }) => {
      set.headers['content-type'] = 'text/plain; version=0.0.4; charset=utf-8';
      return telemetryCollector.toPrometheusText();
    });
}

