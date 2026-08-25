import { describe, it, expect, beforeAll, afterAll } from 'bun:test';
import { createApp } from '../src/index';

describe('Server-Sent Events (SSE) Proxying', () => {
  let mockServer: any;
  const mockPort = 8803;
  const edgePort = 8802;
  let edgeApp: any;
  let edgeServer: any;

  beforeAll(async () => {
    mockServer = Bun.serve({
      port: mockPort,
      hostname: '127.0.0.1',
      async fetch(req) {
        const url = new URL(req.url);
        if (url.pathname === '/v1/chat/stream') {
          // Stream SSE chunks
          const stream = new ReadableStream({
            async start(controller) {
              const encoder = new TextEncoder();
              const tokens = ['Hello', ' ', 'Dr. Watson,', ' ', 'patient vitals are normal.'];
              for (const token of tokens) {
                const chunk = `data: ${JSON.stringify({ token })}\n\n`;
                controller.enqueue(encoder.encode(chunk));
                await Bun.sleep(10);
              }
              controller.enqueue(encoder.encode('data: [DONE]\n\n'));
              controller.close();
            },
          });

          return new Response(stream, {
            headers: {
              'Content-Type': 'text/event-stream',
              'Cache-Control': 'no-cache',
              'Connection': 'keep-alive',
            },
          });
        }

        return new Response('Not Found', { status: 404 });
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

  it('proxies SSE streaming responses without buffering', async () => {
    const res = await fetch(`http://127.0.0.1:${edgePort}/v1/chat/stream`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: 'Status check' }),
    });

    expect(res.status).toBe(200);
    expect(res.headers.get('content-type')).toContain('text/event-stream');

    const reader = res.body?.getReader();
    expect(reader).toBeTruthy();

    const decoder = new TextDecoder();
    let accumulated = '';

    while (reader) {
      const { done, value } = await reader.read();
      if (done) break;
      accumulated += decoder.decode(value, { stream: true });
    }

    expect(accumulated).toContain('Dr. Watson');
    expect(accumulated).toContain('[DONE]');
  });
});
