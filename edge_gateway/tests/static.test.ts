import { describe, it, expect, beforeAll, afterAll } from 'bun:test';
import { createApp } from '../src/index';
import { getMimeType } from '../src/static';
import path from 'path';
import fs from 'fs';

describe('Static Asset & SPA Fallback Server', () => {
  const testDir = path.resolve(process.cwd(), 'tests/fixtures/dist');
  let app: any;

  beforeAll(() => {
    // Create fixture directory with mock index.html and assets
    fs.mkdirSync(path.join(testDir, 'assets'), { recursive: true });
    fs.writeFileSync(
      path.join(testDir, 'index.html'),
      '<!DOCTYPE html><html><head><title>SPA App</title></head><body><div id="root">SPA Root</div></body></html>'
    );
    fs.writeFileSync(
      path.join(testDir, 'assets/app-12345.js'),
      'console.log("SPA Bundle");'
    );
    fs.writeFileSync(
      path.join(testDir, 'assets/style-12345.css'),
      'body { background: #000; }'
    );
    fs.writeFileSync(
      path.join(testDir, 'favicon.ico'),
      'binary-favicon-data'
    );

    app = createApp({
      configOverride: {
        staticDir: 'tests/fixtures/dist',
        rustBackendUrl: 'http://127.0.0.1:8999',
      },
    });
  });

  afterAll(() => {
    // Clean up test fixture
    try {
      fs.rmSync(path.resolve(process.cwd(), 'tests/fixtures'), { recursive: true, force: true });
    } catch (_) {}
  });

  it('correctly maps file extensions to MIME types', () => {
    expect(getMimeType('app.js')).toBe('application/javascript; charset=utf-8');
    expect(getMimeType('index.html')).toBe('text/html; charset=utf-8');
    expect(getMimeType('style.css')).toBe('text/css; charset=utf-8');
    expect(getMimeType('logo.svg')).toBe('image/svg+xml');
    expect(getMimeType('icon.png')).toBe('image/png');
    expect(getMimeType('doc.pdf')).toBe('application/pdf');
    expect(getMimeType('model.wasm')).toBe('application/wasm');
  });

  it('serves static hashed asset with immutable cache headers', async () => {
    const res = await app.handle(new Request('http://127.0.0.1:8000/assets/app-12345.js'));
    expect(res.status).toBe(200);
    expect(res.headers.get('content-type')).toBe('application/javascript; charset=utf-8');
    expect(res.headers.get('cache-control')).toBe('public, max-age=31536000, immutable');
    const content = await res.text();
    expect(content).toBe('console.log("SPA Bundle");');
  });

  it('serves root URL index.html with no-cache headers', async () => {
    const res = await app.handle(new Request('http://127.0.0.1:8000/'));
    expect(res.status).toBe(200);
    expect(res.headers.get('content-type')).toBe('text/html; charset=utf-8');
    expect(res.headers.get('cache-control')).toContain('no-cache');
    const html = await res.text();
    expect(html).toContain('SPA Root');
  });

  it('falls back to index.html for client-side SPA routes', async () => {
    const res = await app.handle(new Request('http://127.0.0.1:8000/dashboard/patients/123'));
    expect(res.status).toBe(200);
    expect(res.headers.get('content-type')).toBe('text/html; charset=utf-8');
    const html = await res.text();
    expect(html).toContain('SPA Root');
  });
});
