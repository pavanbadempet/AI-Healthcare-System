/**
 * Request Context & Telemetry Middleware
 * Injects X-Request-ID, measures request duration, and performs safe, non-PII access logging.
 */

import { Elysia } from 'elysia';

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
    const durationMs = (performance.now() - (startTime || performance.now())).toFixed(2);
    set.headers['x-request-id'] = requestId || '';
    set.headers['x-response-time'] = `${durationMs}ms`;

    // Only log non-PII metadata (method, pathname, status, duration, IP, request ID)
    const url = new URL(request.url);
    if (process.env.NODE_ENV !== 'test' && !url.pathname.startsWith('/health')) {
      const status = set.status || 200;
      console.log(`[EDGE] ${request.method} ${url.pathname} -> ${status} (${durationMs}ms) [req_id=${requestId}]`);
    }
  });
