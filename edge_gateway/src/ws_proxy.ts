/**
 * Transparent WebSocket Proxy Module
 * Bi-directional streaming bridge between browser clients and the Rust Axum WebSocket server.
 */

import { Elysia } from 'elysia';
import { config } from './config';

interface WsProxyState {
  upstreamWs: WebSocket | null;
  messageQueue: (string | ArrayBuffer | Uint8Array)[];
  isUpstreamOpen: boolean;
}

function normalizeMessage(message: any): string | ArrayBuffer | Uint8Array {
  if (typeof message === 'object' && !(message instanceof ArrayBuffer || ArrayBuffer.isView(message))) {
    return JSON.stringify(message);
  }
  return message;
}

export function createWsProxyPlugin(targetWsBaseUrl: string = config.rustWsUrl) {
  const connectionMap = new Map<string, WsProxyState>();

  function setupUpstream(ws: any, pathname: string, search: string) {
    const wsId = ws.id || String(Math.random());
    const upstreamUrl = `${targetWsBaseUrl}${pathname}${search}`;
    const state: WsProxyState = {
      upstreamWs: null,
      messageQueue: [],
      isUpstreamOpen: false,
    };
    connectionMap.set(wsId, state);
    if (ws.data) {
      ws.data._wsProxyId = wsId;
    }

    try {
      const upstream = new WebSocket(upstreamUrl);
      state.upstreamWs = upstream;
      upstream.binaryType = 'arraybuffer';

      upstream.onopen = () => {
        state.isUpstreamOpen = true;
        // Flush any queued messages from client
        while (state.messageQueue.length > 0) {
          const msg = state.messageQueue.shift();
          if (msg !== undefined) {
            upstream.send(msg);
          }
        }
      };

      upstream.onmessage = (event) => {
        try {
          ws.send(event.data);
        } catch (err) {
          console.error('[WS PROXY] Error forwarding to client:', err);
        }
      };

      upstream.onerror = (err) => {
        console.error('[WS PROXY] Upstream WebSocket error:', upstreamUrl, err);
      };

      upstream.onclose = (event) => {
        state.isUpstreamOpen = false;
        connectionMap.delete(wsId);
        try {
          ws.close(event.code || 1000, event.reason || 'Upstream closed');
        } catch (_) {}
      };
    } catch (err) {
      console.error('[WS PROXY] Failed to initialize upstream WS:', err);
      connectionMap.delete(wsId);
      try {
        ws.close(1011, 'Backend WebSocket unavailable');
      } catch (_) {}
    }
  }

  function handleClientMessage(ws: any, rawMessage: any) {
    const wsId = ws.id || ws.data?._wsProxyId;
    const state = connectionMap.get(wsId);
    if (!state || !state.upstreamWs) return;

    const message = normalizeMessage(rawMessage);

    if (state.isUpstreamOpen && state.upstreamWs.readyState === WebSocket.OPEN) {
      state.upstreamWs.send(message);
    } else {
      state.messageQueue.push(message);
    }
  }

  function handleClientClose(ws: any) {
    const wsId = ws.id || ws.data?._wsProxyId;
    const state = connectionMap.get(wsId);
    if (state && state.upstreamWs) {
      try {
        if (state.upstreamWs.readyState === WebSocket.OPEN || state.upstreamWs.readyState === WebSocket.CONNECTING) {
          state.upstreamWs.close(1000, 'Client disconnected');
        }
      } catch (_) {}
    }
    if (wsId) {
      connectionMap.delete(wsId);
    }
  }

  return new Elysia({ name: 'plugin:ws-proxy' })
    .ws('/v1/telemetry/stream', {
      open(ws) {
        const url = new URL(ws.data.request.url);
        setupUpstream(ws, '/v1/telemetry/stream', url.search);
      },
      message(ws, message) {
        handleClientMessage(ws, message);
      },
      close(ws) {
        handleClientClose(ws);
      },
    })
    .ws('/v1/telemetry/vitals/:id', {
      open(ws) {
        const url = new URL(ws.data.request.url);
        const id = ws.data.params.id;
        setupUpstream(ws, `/v1/telemetry/vitals/${id}`, url.search);
      },
      message(ws, message) {
        handleClientMessage(ws, message);
      },
      close(ws) {
        handleClientClose(ws);
      },
    })
    .ws('/ws/*', {
      open(ws) {
        const url = new URL(ws.data.request.url);
        setupUpstream(ws, url.pathname, url.search);
      },
      message(ws, message) {
        handleClientMessage(ws, message);
      },
      close(ws) {
        handleClientClose(ws);
      },
    });
}
