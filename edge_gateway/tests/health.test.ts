import { describe, it, expect, beforeAll, afterAll } from 'bun:test';
import { createApp } from '../src/index';

describe('Health & Readiness Aggregator', () => {
  let mockBackend: any;
  const mockPort = 8807;
  let app: any;

  beforeAll(() => {
    mockBackend = Bun.serve({
      port: mockPort,
      hostname: '127.0.0.1',
      fetch(req) {
        const url = new URL(req.url);
        if (url.pathname === '/healthz') {
          return new Response(JSON.stringify({ status: 'ok', engine: 'rust-axum', db: 'connected' }), {
            headers: { 'Content-Type': 'application/json' },
          });
        }
        return new Response('Not Found', { status: 404 });
      },
    });

    app = createApp({
      configOverride: {
        rustBackendUrl: `http://127.0.0.1:${mockPort}`,
        staticDir: 'non_existent_dir_for_test',
      },
    });
  });

  afterAll(() => {
    if (mockBackend) mockBackend.stop();
  });

  it('responds to /healthz/live with alive status', async () => {
    const res = await app.handle(new Request('http://127.0.0.1:8000/healthz/live'));
    expect(res.status).toBe(200);
    const data: any = await res.json();
    expect(data.status).toBe('alive');
    expect(data.timestamp).toBeTruthy();
  });

  it('aggregates edge and backend status on /health', async () => {
    const res = await app.handle(new Request('http://127.0.0.1:8000/health'));
    expect(res.status).toBe(200);
    const data: any = await res.json();
    expect(data.status).toBe('healthy');
    expect(data.edge.status).toBe('ok');
    expect(data.edge.runtime).toBe('bun');
    expect(data.edge.memory).toBeTruthy();
    expect(data.backend.status).toBe('ok');
    expect(data.backend.details.engine).toBe('rust-axum');
  });

  it('returns readiness status on /healthz/ready', async () => {
    const res = await app.handle(new Request('http://127.0.0.1:8000/healthz/ready'));
    expect(res.status).toBe(200);
    const data: any = await res.json();
    expect(data.status).toBe('ready');
    expect(data.backend.status).toBe('ok');
  });

  it('reports degraded status when backend is down', async () => {
    const disconnectedApp = createApp({
      configOverride: {
        rustBackendUrl: 'http://127.0.0.1:59998', // Offline port
      },
    });

    const res = await disconnectedApp.handle(new Request('http://127.0.0.1:8000/health'));
    expect(res.status).toBe(200);
    const data: any = await res.json();
    expect(data.status).toBe('degraded');
    expect(data.edge.status).toBe('ok');
    expect(data.backend.status).toBe('unreachable');
  });
});
