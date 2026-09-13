import { Elysia } from 'elysia';
import { metricsRegistry } from '../metrics';

export interface RequestMeta {
  requestId: string;
  startTime: number;
  clientIp: string;
}

export function extractClientIp(headers: Headers, remoteAddress?: string): string {
  const forwardedFor = headers.get('x-forwarded-for');
  if (forwardedFor) {
    const first = forwardedFor.split(',')[0].trim();
    if (first) return first;
  }
  const realIp = headers.get('x-real-ip');
  if (realIp) return realIp.trim();

  return remoteAddress || '127.0.0.1';
}

export const requestContext = new Elysia({ name: 'middleware:request-context' })
  .derive({ as: 'global' }, ({ request, server }) => {
    const existingId = request.headers.get('x-request-id');
    const requestId = existingId || crypto.randomUUID();
    const startTime = performance.now();
    const clientIp = extractClientIp(request.headers);

    return {
      requestId,
      startTime,
      clientIp,
    };
  })
  .onAfterResponse({ as: 'global' }, ({ request, set, requestId, startTime, clientIp }) => {
    const durationNum = performance.now() - (startTime || performance.now());
    const durationMs = durationNum.toFixed(2);
    set.headers['x-request-id'] = requestId || '';
    set.headers['x-response-time'] = `${durationMs}ms`;

    const url = new URL(request.url);
    const status = (typeof set.status === 'number') ? set.status : 200;

    // Track latency & count in Prometheus metrics registry
    const target = url.pathname.startsWith('/v1/agentic') || url.pathname.startsWith('/v1/clinical-agents')
      ? 'python'
      : (url.pathname.startsWith('/health') || url.pathname.startsWith('/metrics') ? 'edge' : 'rust');
    metricsRegistry.recordRequest(target, request.method, status, durationNum / 1000.0);

    // Only log non-PII metadata (method, pathname, status, duration, IP, request ID)
    if (process.env.NODE_ENV !== 'test' && !url.pathname.startsWith('/health')) {
      console.log(`[EDGE] ${request.method} ${url.pathname} -> ${status} (${durationMs}ms) [req_id=${requestId}]`);
    }
  });

