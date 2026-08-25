import { describe, it, expect, beforeAll, afterAll } from 'bun:test';
import { createApp } from '../src/index';

describe('HTTP Reverse Proxy Plugin', () => {
  let mockServer: any;
  const mockPort = 8801;
  const edgePort = 8800;
  let edgeApp: any;
  let edgeServer: any;

  beforeAll(async () => {
    // Mock upstream backend server
    mockServer = Bun.serve({
      port: mockPort,
      hostname: '127.0.0.1',
      async fetch(req) {
        const url = new URL(req.url);
        const auth = req.headers.get('authorization');
        const xReqId = req.headers.get('x-request-id');
        const xFwdFor = req.headers.get('x-forwarded-for');
        const customHeader = req.headers.get('x-ai-provider');

        if (url.pathname === '/v1/predict/diabetes') {
          const body = await req.json();
          return new Response(JSON.stringify({
            prediction: 1,
            probability: 0.85,
            risk_level: 'High',
            received_body: body,
            received_auth: auth,
            received_x_req_id: xReqId,
            received_x_fwd_for: xFwdFor,
            received_custom_header: customHeader,
          }), {
            headers: { 'Content-Type': 'application/json', 'X-Custom-Upstream': 'true' },
          });
        }

        if (url.pathname === '/v1/patients') {
          const skip = url.searchParams.get('skip');
          const limit = url.searchParams.get('limit');
          return new Response(JSON.stringify({
            patients: [{ id: 1, name: 'Test Patient' }],
            skip,
            limit,
          }), {
            headers: { 'Content-Type': 'application/json' },
          });
        }

        if (url.pathname === '/docs') {
          return new Response('<html><body>API Documentation</body></html>', {
            headers: { 'Content-Type': 'text/html' },
          });
        }

        if (url.pathname === '/openapi.json') {
          return new Response(JSON.stringify({ openapi: '3.0.0', info: { title: 'Healthcare API' } }), {
            headers: { 'Content-Type': 'application/json' },
          });
        }

        return new Response(JSON.stringify({ error: 'Not found' }), {
          status: 404,
          headers: { 'Content-Type': 'application/json' },
        });
      },
    });

    edgeApp = createApp({
      configOverride: {
        port: edgePort,
        host: '127.0.0.1',
        rustBackendUrl: `http://127.0.0.1:${mockPort}`,
        rustWsUrl: `ws://127.0.0.1:${mockPort}`,
        rateLimitPerMinute: 1000,
        rateLimitBurst: 500,
      },
    });

    edgeServer = edgeApp.listen({ port: edgePort, hostname: '127.0.0.1' });
  });

  afterAll(() => {
    if (mockServer) mockServer.stop();
    if (edgeServer) edgeServer.stop();
  });

  it('proxies POST requests with body, headers, and response serialization', async () => {
    const payload = { glucose: 140, bmi: 31.2, age: 45 };
    const res = await fetch(`http://127.0.0.1:${edgePort}/v1/predict/diabetes`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer test-token-123',
        'X-AI-Provider': 'gemini',
      },
      body: JSON.stringify(payload),
    });

    expect(res.status).toBe(200);
    expect(res.headers.get('x-custom-upstream')).toBe('true');
    expect(res.headers.get('x-request-id')).toBeTruthy();

    const data: any = await res.json();
    expect(data.prediction).toBe(1);
    expect(data.probability).toBe(0.85);
    expect(data.received_body).toEqual(payload);
    expect(data.received_auth).toBe('Bearer test-token-123');
    expect(data.received_custom_header).toBe('gemini');
    expect(data.received_x_fwd_for).toBeTruthy();
  });

  it('preserves query parameters on GET requests', async () => {
    const res = await fetch(`http://127.0.0.1:${edgePort}/v1/patients?skip=10&limit=25`);
    expect(res.status).toBe(200);
    const data: any = await res.json();
    expect(data.skip).toBe('10');
    expect(data.limit).toBe('25');
    expect(data.patients.length).toBe(1);
  });

  it('proxies /docs and /openapi.json specification endpoints', async () => {
    const docsRes = await fetch(`http://127.0.0.1:${edgePort}/docs`);
    expect(docsRes.status).toBe(200);
    const docsText = await docsRes.text();
    expect(docsText).toContain('API Documentation');

    const openapiRes = await fetch(`http://127.0.0.1:${edgePort}/openapi.json`);
    expect(openapiRes.status).toBe(200);
    const openapiData: any = await openapiRes.json();
    expect(openapiData.openapi).toBe('3.0.0');
  });

  it('returns 502 Bad Gateway when backend is unreachable', async () => {
    const deadPortApp = createApp({
      configOverride: {
        port: 8899,
        host: '127.0.0.1',
        rustBackendUrl: 'http://127.0.0.1:59999', // Non-existent port
      },
    });

    const res = await deadPortApp.handle(
      new Request('http://127.0.0.1:8899/v1/predict/heart')
    );

    expect(res.status).toBe(502);
    const errData: any = await res.json();
    expect(errData.error).toBe('Bad Gateway');
    expect(errData.status).toBe(502);
  });
});
