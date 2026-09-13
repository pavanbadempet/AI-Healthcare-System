/**
 * Bun Native Real-Time Telemetry & Token Streaming Hub
 * High-concurrency Server-Sent Events (SSE) and pub/sub engine for
 * bedside vital signs, continuous ECG streaming, and LLM agent token deltas.
 */

import { Elysia, t } from 'elysia';

export interface TelemetryEvent {
  id?: string;
  event?: string;
  data: any;
  timestamp?: number;
}

export interface ClientConnection {
  id: string;
  channel: string;
  patientId?: string;
  controller: ReadableStreamDefaultController<Uint8Array>;
  connectedAt: number;
}

export class TelemetryHub {
  private static instance: TelemetryHub;
  private clients: Map<string, ClientConnection> = new Map();
  private channelIndex: Map<string, Set<string>> = new Map();
  private totalEventsBroadcast: number = 0;
  private encoder: TextEncoder = new TextEncoder();

  private constructor() {}

  public static getInstance(): TelemetryHub {
    if (!TelemetryHub.instance) {
      TelemetryHub.instance = new TelemetryHub();
    }
    return TelemetryHub.instance;
  }

  /**
   * Register a new SSE subscriber client
   */
  public registerClient(
    id: string,
    channel: string,
    controller: ReadableStreamDefaultController<Uint8Array>,
    patientId?: string
  ): void {
    const conn: ClientConnection = {
      id,
      channel,
      patientId,
      controller,
      connectedAt: Date.now(),
    };

    this.clients.set(id, conn);

    if (!this.channelIndex.has(channel)) {
      this.channelIndex.set(channel, new Set());
    }
    this.channelIndex.get(channel)!.add(id);

    // Initial handshake ping
    this.sendToClient(conn, {
      event: 'connected',
      data: {
        clientId: id,
        channel,
        patientId: patientId || null,
        status: 'subscribed',
        timestamp: Date.now(),
      },
    });
  }

  /**
   * Unregister an SSE subscriber
   */
  public unregisterClient(id: string): void {
    const conn = this.clients.get(id);
    if (!conn) return;

    const channelSet = this.channelIndex.get(conn.channel);
    if (channelSet) {
      channelSet.delete(id);
      if (channelSet.size === 0) {
        this.channelIndex.delete(conn.channel);
      }
    }

    this.clients.delete(id);
  }

  /**
   * Broadcast a telemetry or agent token event to all channel subscribers
   */
  public broadcast(channel: string, event: TelemetryEvent, targetPatientId?: string): number {
    const subscriberIds = this.channelIndex.get(channel);
    if (!subscriberIds || subscriberIds.size === 0) {
      return 0;
    }

    let deliveredCount = 0;
    for (const clientId of subscriberIds) {
      const client = this.clients.get(clientId);
      if (!client) continue;

      if (targetPatientId && client.patientId && client.patientId !== targetPatientId) {
        continue;
      }

      try {
        this.sendToClient(client, event);
        deliveredCount++;
      } catch {
        this.unregisterClient(clientId);
      }
    }

    this.totalEventsBroadcast++;
    return deliveredCount;
  }

  /**
   * Format and send an SSE frame to a single client
   */
  private sendToClient(client: ClientConnection, event: TelemetryEvent): void {
    let frame = '';
    if (event.id) {
      frame += `id: ${event.id}\n`;
    }
    if (event.event) {
      frame += `event: ${event.event}\n`;
    }

    const payload = typeof event.data === 'string' ? event.data : JSON.stringify(event.data);
    frame += `data: ${payload}\n\n`;

    client.controller.enqueue(this.encoder.encode(frame));
  }

  /**
   * Hub health and load metrics
   */
  public getStats() {
    const channels: Record<string, number> = {};
    for (const [ch, set] of this.channelIndex.entries()) {
      channels[ch] = set.size;
    }

    return {
      activeConnections: this.clients.size,
      activeChannels: this.channelIndex.size,
      totalEventsBroadcast: this.totalEventsBroadcast,
      channels,
    };
  }

  /**
   * Reset for clean testing
   */
  public clear(): void {
    for (const client of this.clients.values()) {
      try {
        client.controller.close();
      } catch {}
    }
    this.clients.clear();
    this.channelIndex.clear();
    this.totalEventsBroadcast = 0;
  }
}

/**
 * Creates the native Bun SSE & Telemetry plugin for Elysia
 */
export function createTelemetryStreamPlugin() {
  const hub = TelemetryHub.getInstance();

  return new Elysia({ name: 'telemetry-stream-plugin' })
    // SSE endpoint for vital signs & telemetry streams
    .get('/v1/telemetry/stream', ({ query }) => {
      const channel = (query.channel as string) || 'vitals';
      const patientId = query.patient_id as string | undefined;
      const clientId = `conn_${Math.random().toString(36).substring(2, 10)}_${Date.now()}`;

      const stream = new ReadableStream({
        start(controller) {
          hub.registerClient(clientId, channel, controller, patientId);
        },
        cancel() {
          hub.unregisterClient(clientId);
        },
      });

      return new Response(stream, {
        headers: {
          'Content-Type': 'text/event-stream',
          'Cache-Control': 'no-cache, no-transform',
          'Connection': 'keep-alive',
          'X-Accel-Buffering': 'no',
          'Access-Control-Allow-Origin': '*',
        },
      });
    })

    // Dedicated SSE endpoint for streaming LLM agent reasoning tokens
    .get('/v1/agentic/stream/:sessionId', ({ params }) => {
      const sessionId = params.sessionId;
      const channel = `agent:${sessionId}`;
      const clientId = `agent_conn_${Math.random().toString(36).substring(2, 10)}_${Date.now()}`;

      const stream = new ReadableStream({
        start(controller) {
          hub.registerClient(clientId, channel, controller);
        },
        cancel() {
          hub.unregisterClient(clientId);
        },
      });

      return new Response(stream, {
        headers: {
          'Content-Type': 'text/event-stream',
          'Cache-Control': 'no-cache, no-transform',
          'Connection': 'keep-alive',
          'X-Accel-Buffering': 'no',
          'Access-Control-Allow-Origin': '*',
        },
      });
    })

    // Ingress broadcast endpoint for upstream services to push telemetry/events
    .post(
      '/v1/telemetry/broadcast',
      ({ body }) => {
        const { channel, event, data, patient_id } = body as {
          channel: string;
          event?: string;
          data: any;
          patient_id?: string;
        };

        const delivered = hub.broadcast(
          channel,
          {
            event: event || 'update',
            data,
            timestamp: Date.now(),
          },
          patient_id
        );

        return {
          status: 'ok',
          channel,
          deliveredTo: delivered,
          timestamp: Date.now(),
        };
      },
      {
        body: t.Object({
          channel: t.String(),
          event: t.Optional(t.String()),
          data: t.Any(),
          patient_id: t.Optional(t.String()),
        }),
      }
    )

    // Telemetry Hub metrics endpoint
    .get('/v1/telemetry/hub/stats', () => {
      return {
        status: 'healthy',
        timestamp: Date.now(),
        ...hub.getStats(),
      };
    });
}
