import { describe, it, expect, beforeEach, afterEach } from 'bun:test';
import { TelemetryHub, createTelemetryStreamPlugin } from '../src/telemetry_stream';
import { Elysia } from 'elysia';

describe('Bun Native TelemetryHub & SSE Streaming Engine', () => {
  let hub: TelemetryHub;

  beforeEach(() => {
    hub = TelemetryHub.getInstance();
    hub.clear();
  });

  afterEach(() => {
    hub.clear();
  });

  it('registers subscriber clients and tracks channel metrics', () => {
    let receivedChunks: Uint8Array[] = [];
    const mockController = {
      enqueue(chunk: Uint8Array) {
        receivedChunks.push(chunk);
      },
      close() {},
    } as unknown as ReadableStreamDefaultController<Uint8Array>;

    hub.registerClient('client-1', 'vitals', mockController, 'pat-999');

    const stats = hub.getStats();
    expect(stats.activeConnections).toBe(1);
    expect(stats.activeChannels).toBe(1);
    expect(stats.channels['vitals']).toBe(1);

    // Initial handshake ping should have been enqueued
    expect(receivedChunks.length).toBe(1);
    const text = new TextDecoder().decode(receivedChunks[0]);
    expect(text).toContain('event: connected');
    expect(text).toContain('pat-999');
  });

  it('broadcasts telemetry events to matching subscribers', () => {
    let client1Chunks: Uint8Array[] = [];
    let client2Chunks: Uint8Array[] = [];

    const ctrl1 = {
      enqueue(chunk: Uint8Array) {
        client1Chunks.push(chunk);
      },
      close() {},
    } as unknown as ReadableStreamDefaultController<Uint8Array>;

    const ctrl2 = {
      enqueue(chunk: Uint8Array) {
        client2Chunks.push(chunk);
      },
      close() {},
    } as unknown as ReadableStreamDefaultController<Uint8Array>;

    hub.registerClient('c1', 'vitals', ctrl1, 'patient-A');
    hub.registerClient('c2', 'vitals', ctrl2, 'patient-B');

    // Broadcast specifically to patient-A
    const delivered1 = hub.broadcast(
      'vitals',
      {
        event: 'vital_update',
        data: { hr: 78, spo2: 99, bp: '120/80' },
      },
      'patient-A'
    );

    expect(delivered1).toBe(1);
    expect(client1Chunks.length).toBe(2); // handshake + vital_update
    expect(client2Chunks.length).toBe(1); // handshake only

    const latestText = new TextDecoder().decode(client1Chunks[1]);
    expect(latestText).toContain('event: vital_update');
    expect(latestText).toContain('"spo2":99');

    // Broadcast globally to all vitals subscribers
    const deliveredAll = hub.broadcast('vitals', {
      event: 'system_alert',
      data: { code: 'CODE_BLUE_CLEARED' },
    });

    expect(deliveredAll).toBe(2);
    expect(client1Chunks.length).toBe(3);
    expect(client2Chunks.length).toBe(2);
  });

  it('unregisters disconnected clients and updates channel metrics', () => {
    const ctrl = {
      enqueue() {},
      close() {},
    } as unknown as ReadableStreamDefaultController<Uint8Array>;

    hub.registerClient('c1', 'alerts', ctrl);
    expect(hub.getStats().activeConnections).toBe(1);

    hub.unregisterClient('c1');
    expect(hub.getStats().activeConnections).toBe(0);
    expect(hub.getStats().activeChannels).toBe(0);
  });

  it('handles broadcast and stats via Elysia HTTP routes', async () => {
    const app = new Elysia().use(createTelemetryStreamPlugin());

    // Check stats
    const statsRes = await app.handle(new Request('http://localhost/v1/telemetry/hub/stats'));
    expect(statsRes.status).toBe(200);
    const stats = await statsRes.json();
    expect(stats.status).toBe('healthy');
    expect(stats.activeConnections).toBe(0);

    // Broadcast event via POST
    const broadcastRes = await app.handle(
      new Request('http://localhost/v1/telemetry/broadcast', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          channel: 'bedside',
          event: 'ecg_rhythm',
          data: { rhythm: 'NSR', rate: 72 },
        }),
      })
    );

    expect(broadcastRes.status).toBe(200);
    const broadcastJson = await broadcastRes.json();
    expect(broadcastJson.status).toBe('ok');
    expect(broadcastJson.channel).toBe('bedside');
  });
});
