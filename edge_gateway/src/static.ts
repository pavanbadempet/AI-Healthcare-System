/**
 * Static Asset & SPA Fallback Server
 * Efficiently serves compiled Vite React 19 SPA assets with caching headers and HTML5 history fallback routing.
 */

import { Elysia } from 'elysia';
import path from 'path';
import { config } from './config';

// Common MIME types map
const MIME_TYPES: Record<string, string> = {
  '.html': 'text/html; charset=utf-8',
  '.js': 'application/javascript; charset=utf-8',
  '.mjs': 'application/javascript; charset=utf-8',
  '.css': 'text/css; charset=utf-8',
  '.json': 'application/json; charset=utf-8',
  '.png': 'image/png',
  '.jpg': 'image/jpeg',
  '.jpeg': 'image/jpeg',
  '.gif': 'image/gif',
  '.svg': 'image/svg+xml',
  '.ico': 'image/x-icon',
  '.webp': 'image/webp',
  '.wasm': 'application/wasm',
  '.woff': 'font/woff',
  '.woff2': 'font/woff2',
  '.ttf': 'font/ttf',
  '.eot': 'application/vnd.ms-fontobject',
  '.pdf': 'application/pdf',
  '.txt': 'text/plain; charset=utf-8',
};

const DEFAULT_FALLBACK_HTML = `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>AI Healthcare System - Edge Gateway</title>
  <style>
    body { font-family: system-ui, -apple-system, sans-serif; background: #0f172a; color: #f8fafc; display: flex; align-items: center; justify-content: center; height: 100vh; margin: 0; }
    .card { background: #1e293b; padding: 2.5rem; border-radius: 1rem; box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.5); max-width: 500px; text-align: center; border: 1px solid #334155; }
    h1 { color: #38bdf8; font-size: 1.75rem; margin-bottom: 0.5rem; }
    p { color: #94a3b8; font-size: 1rem; line-height: 1.5; }
    .badge { display: inline-block; background: #0369a1; color: #e0f2fe; padding: 0.25rem 0.75rem; border-radius: 9999px; font-size: 0.875rem; font-weight: 600; margin-top: 1rem; }
    .links { margin-top: 1.5rem; display: flex; justify-content: center; gap: 1rem; }
    a { color: #38bdf8; text-decoration: none; font-weight: 500; }
    a:hover { text-decoration: underline; }
  </style>
</head>
<body>
  <div class="card">
    <h1>AI Healthcare System</h1>
    <p>Bun + ElysiaJS Edge Gateway is running and ready.</p>
    <div class="badge">Tier 1 Edge Gateway Active</div>
    <div class="links">
      <a href="/health">Health Status</a>
      <a href="/docs">API Docs</a>
      <a href="http://127.0.0.1:3000" target="_blank">Frontend Dev Server (Port 3000)</a>
    </div>
  </div>
</body>
</html>`;

export function getMimeType(filePath: string): string {
  const ext = path.extname(filePath).toLowerCase();
  return MIME_TYPES[ext] || 'application/octet-stream';
}

export function isApiOrSpecialRoute(pathname: string): boolean {
  return (
    pathname === '/v1' ||
    pathname.startsWith('/v1/') ||
    pathname === '/api' ||
    pathname.startsWith('/api/') ||
    pathname === '/health' ||
    pathname.startsWith('/health/') ||
    pathname === '/healthz' ||
    pathname.startsWith('/healthz/') ||
    pathname === '/metrics' ||
    pathname === '/docs' ||
    pathname.startsWith('/docs/') ||
    pathname === '/openapi.json' ||
    pathname === '/redoc' ||
    pathname.startsWith('/ws/')
  );
}

export async function serveSpaIndex(resolvedDir: string): Promise<Response> {
  const indexPath = path.join(resolvedDir, 'index.html');
  const indexFile = Bun.file(indexPath);

  if (await indexFile.exists()) {
    return new Response(indexFile, {
      status: 200,
      headers: {
        'Content-Type': 'text/html; charset=utf-8',
        'Cache-Control': 'no-cache, no-store, must-revalidate',
      },
    });
  }

  return new Response(DEFAULT_FALLBACK_HTML, {
    status: 200,
    headers: {
      'Content-Type': 'text/html; charset=utf-8',
      'Cache-Control': 'no-cache',
    },
  });
}

export function createStaticSpaPlugin(staticDir: string = config.staticDir) {
  const resolvedDir = path.resolve(process.cwd(), staticDir);

  return new Elysia({ name: 'plugin:static-spa' })
    // Root path handler
    .get('/', async () => {
      return serveSpaIndex(resolvedDir);
    })
    // Explicit static asset handlers
    .get('/assets/*', async ({ request, set }) => {
      const url = new URL(request.url);
      const sanitized = path.normalize(url.pathname).replace(/^(\.\.[\/\\])+/, '');
      const targetFilePath = path.join(resolvedDir, sanitized);
      const file = Bun.file(targetFilePath);

      if (await file.exists()) {
        const mime = getMimeType(targetFilePath);
        set.headers['Content-Type'] = mime;
        set.headers['Cache-Control'] = 'public, max-age=31536000, immutable';
        return file;
      }
      set.status = 404;
      return { error: 'Asset Not Found', path: url.pathname };
    })
    .get('/favicon.ico', async ({ set }) => {
      const target = path.join(resolvedDir, 'favicon.ico');
      const file = Bun.file(target);
      if (await file.exists()) {
        set.headers['Content-Type'] = 'image/x-icon';
        set.headers['Cache-Control'] = 'public, max-age=86400';
        return file;
      }
      set.status = 404;
      return 'Not found';
    })
    // 404 handler for SPA fallback and API errors (registered globally)
    .onError({ as: 'global' }, ({ code, request, set }) => {
      if (code === 'NOT_FOUND') {
        const url = new URL(request.url);
        const pathname = url.pathname;

        // If it's an API route that didn't match
        if (isApiOrSpecialRoute(pathname)) {
          set.status = 404;
          return {
            error: 'Not Found',
            message: `Endpoint ${request.method} ${pathname} not found`,
            status: 404,
          };
        }

        // For non-API GET requests, serve SPA HTML fallback with 200 OK
        if (request.method === 'GET') {
          set.status = 200;
          return serveSpaIndex(resolvedDir);
        }
      }
    });
}
