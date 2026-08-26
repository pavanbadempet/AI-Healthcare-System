/**
 * High-Performance Reverse Proxy Module
 * Forwards HTTP requests and Server-Sent Events (SSE) streams to the Rust Axum backend with <5ms overhead.
 */

import { Elysia } from 'elysia';
import { config } from './config';
import { extractClientIp } from './middleware/request_context';

const HOP_BY_HOP_HEADERS = new Set([
  'connection',
  'keep-alive',
  'proxy-authenticate',
  'proxy-authorization',
  'te',
  'trailers',
  'transfer-encoding',
  'upgrade',
  'host',
]);

export interface ProxyOptions {
  targetBaseUrl?: string;
}

export async function forwardHttpRequest(
  request: Request,
  targetBaseUrl: string = config.rustBackendUrl,
  clientIp?: string
): Promise<Response> {
  const startTime = performance.now();
  const url = new URL(request.url);
  const targetUrl = new URL(url.pathname + url.search, targetBaseUrl);

  const ip = clientIp || extractClientIp(request.headers);
  const existingForwarded = request.headers.get('x-forwarded-for');
  const forwardedFor = existingForwarded ? `${existingForwarded}, ${ip}` : ip;

  // Build upstream headers
  const upstreamHeaders = new Headers();
  for (const [key, value] of request.headers.entries()) {
    const lowerKey = key.toLowerCase();
    if (!HOP_BY_HOP_HEADERS.has(lowerKey)) {
      upstreamHeaders.set(key, value);
    }
  }

  // Inject proxy tracking headers
  upstreamHeaders.set('x-forwarded-for', forwardedFor);
  upstreamHeaders.set('x-real-ip', ip);
  upstreamHeaders.set('x-forwarded-proto', url.protocol.replace(':', ''));
  upstreamHeaders.set('x-forwarded-host', url.host);

  const requestId = request.headers.get('x-request-id') || crypto.randomUUID();
  upstreamHeaders.set('x-request-id', requestId);

  // Determine if request has body
  const method = request.method.toUpperCase();
  const hasBody = method !== 'GET' && method !== 'HEAD';
  const body = hasBody ? request.body : undefined;

  try {
    const upstreamResponse = await fetch(targetUrl.toString(), {
      method,
      headers: upstreamHeaders,
      body,
      // @ts-ignore - Bun-specific duplex streaming option
      duplex: hasBody ? 'half' : undefined,
      redirect: 'manual',
    });

    // Build downstream response headers
    const downstreamHeaders = new Headers();
    for (const [key, value] of upstreamResponse.headers.entries()) {
      const lowerKey = key.toLowerCase();
      if (!HOP_BY_HOP_HEADERS.has(lowerKey)) {
        downstreamHeaders.set(key, value);
      }
    }

    const durationMs = (performance.now() - startTime).toFixed(2);
    downstreamHeaders.set('x-request-id', requestId);
    downstreamHeaders.set('x-response-time', `${durationMs}ms`);

    const contentType = upstreamResponse.headers.get('content-type') || '';
    const isEventStream = contentType.includes('text/event-stream');

    if (isEventStream) {
      downstreamHeaders.set('Content-Type', 'text/event-stream');
      downstreamHeaders.set('Cache-Control', 'no-cache, no-transform');
      downstreamHeaders.set('Connection', 'keep-alive');
      downstreamHeaders.set('X-Accel-Buffering', 'no');
    }

    return new Response(upstreamResponse.body, {
      status: upstreamResponse.status,
      statusText: upstreamResponse.statusText,
      headers: downstreamHeaders,
    });
  } catch (error: any) {
    const durationMs = (performance.now() - startTime).toFixed(2);
    const errorDetails = {
      error: 'Bad Gateway',
      message: 'Rust backend unreachable or starting up',
      target: targetUrl.toString(),
      details: error.message || 'ECONNREFUSED',
      status: 502,
    };

    return new Response(JSON.stringify(errorDetails), {
      status: 502,
      headers: {
        'Content-Type': 'application/json',
        'Cache-Control': 'no-store',
        'x-request-id': requestId,
        'x-response-time': `${durationMs}ms`,
      },
    });
  }
}

/**
 * Creates Elysia Reverse Proxy Plugin
 */
export function createProxyPlugin(options: ProxyOptions = {}) {
  const target = options.targetBaseUrl || config.rustBackendUrl;

  return new Elysia({ name: 'plugin:reverse-proxy' })
    .all('/v1', async ({ request }) => forwardHttpRequest(request, target))
    .all('/v1/*', async ({ request }) => forwardHttpRequest(request, target))
    .all('/api', async ({ request }) => forwardHttpRequest(request, target))
    .all('/api/*', async ({ request }) => forwardHttpRequest(request, target))
    .all('/docs', async ({ request }) => forwardHttpRequest(request, target))
    .all('/docs/*', async ({ request }) => forwardHttpRequest(request, target))
    .all('/openapi.json', async ({ request }) => forwardHttpRequest(request, target))
    .all('/redoc', async ({ request }) => forwardHttpRequest(request, target))
    .all('/metrics', async ({ request }) => forwardHttpRequest(request, target))
    .all('/token', async ({ request }) => forwardHttpRequest(request, target))
    .all('/login', async ({ request }) => forwardHttpRequest(request, target))
    .all('/signup', async ({ request }) => forwardHttpRequest(request, target));
}
