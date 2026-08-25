import { describe, it, expect, beforeAll, afterAll } from 'bun:test';
import { createApp } from '../src/index';

describe('WebSocket Proxy Plugin', () => {
  let mockServer: any;
  const mockPort = 8805;
  const edgePort = 8804;
  let edgeApp: any;
  let edgeServer: any;

  beforeAll(async () => {
    // Mock upstream WebSocket server
    mockServer = Bun.serve({
      port: mockPort,
      hostname: '127.0.0.1',
      websocket: {
        open(ws) {
          ws.send(JSON.stringify({ type: 'connected', msg: 'Welcome to Telemetry' }));
        },
        message(ws, message) {
          const parsed = JSON.parse(String(message));
          if (parsed.action === 'ping') {
            ws.send(JSON.stringify({ type: 'pong', timestamp: Date.now() }));
          } else if (parsed.action === 'subscribe_vitals') {
            ws.send(JSON.stringify({
              type: 'vitals_update',
              heart_rate: 72,
              spo2: 98,
              bp_systolic: 120,
              bp_diastolic: 80,
            }));
          }
        },
        close(ws) {},
      },
      fetch(req, server) {
        if (server.upgrade(req)) {
          return;
        }
        return new Response('Expected websocket', { status: 400 });
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

  it('proxies WebSocket telemetry stream bi-directionally', async () => {
    const wsUrl = `ws://127.0.0.1:${edgePort}/v1/telemetry/stream?token=valid_token`;
    const clientWs = new WebSocket(wsUrl);

    const messages: any[] = [];

    await new Promise<void>((resolve, reject) => {
      const timeout = setTimeout(() => reject(new Error('WS Test Timeout')), 3000);

      clientWs.onopen = () => {
        clientWs.send(JSON.stringify({ action: 'ping' }));
        clientWs.send(JSON.stringify({ action: 'subscribe_vitals' }));
      };

      clientWs.onmessage = (event) => {
        const msg = JSON.parse(String(event.data));
        messages.push(msg);

        if (messages.length >= 3) {
          clearTimeout(timeout);
          clientWs.close();
          resolve();
        }
      };

      clientWs.onerror = (err) => {
        clearTimeout(timeout);
        reject(err);
      };
    });

    expect(messages.length).toBeGreaterThanOrEqual(3);
    expect(messages.some(m => m.type === 'connected')).toBe(true);
    expect(messages.some(m => m.type === 'pong')).toBe(true);
    expect(messages.some(m => m.type === 'vitals_update' && m.heart_rate === 72)).toBe(true);
  });
});
