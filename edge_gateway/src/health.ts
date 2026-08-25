/**
 * Health Aggregation & Readiness Monitoring
 * Consolidates Edge Gateway metrics and upstream Rust backend probes into unified health endpoints.
 */

import { Elysia } from 'elysia';
import { config } from './config';

export interface BackendHealthProbe {
  status: 'ok' | 'degraded' | 'unreachable';
  latencyMs: number;
  url: string;
  details?: any;
  error?: string;
}

export async function probeRustBackend(targetUrl: string = config.rustBackendUrl, timeoutMs: number = 1000): Promise<BackendHealthProbe> {
  const probeUrl = `${targetUrl}/healthz`;
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
        latencyMs,
        url: probeUrl,
        details: data || { status: 'ok' },
      };
    } else {
      return {
        status: 'degraded',
        latencyMs,
        url: probeUrl,
        error: `HTTP ${response.status} ${response.statusText}`,
      };
    }
  } catch (error: any) {
    const latencyMs = parseFloat((performance.now() - startTime).toFixed(2));
    return {
      status: 'unreachable',
      latencyMs,
      url: probeUrl,
      error: error.name === 'AbortError' ? 'Probe timed out' : error.message || 'Connection refused',
    };
  }
}

export function createHealthPlugin(targetBackendUrl: string = config.rustBackendUrl) {
  return new Elysia({ name: 'plugin:health-aggregator' })
    .get('/healthz/live', () => ({
      status: 'alive',
      timestamp: new Date().toISOString(),
    }))
    .get('/healthz/ready', async ({ set }) => {
      const backend = await probeRustBackend(targetBackendUrl);
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
      const backend = await probeRustBackend(targetBackendUrl);

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
      const backend = await probeRustBackend(targetBackendUrl);

      return {
        status: backend.status === 'ok' ? 'ok' : 'degraded',
        edge_status: 'ok',
        backend_status: backend.status,
        timestamp: new Date().toISOString(),
        uptime_seconds: Math.floor(process.uptime()),
        memory_mb: +(mem.rss / (1024 * 1024)).toFixed(2),
        backend,
      };
    });
}
