/**
 * AI Healthcare System — Real-Time Telemetry Hook
 * 
 * Connects to the backend WebSocket telemetry stream and provides
 * live-updating hospital operations data to any component.
 * 
 * Features:
 * - Auto-reconnect with exponential backoff
 * - Connection state tracking
 * - Graceful cleanup on unmount
 */

import { useState, useEffect, useRef, useCallback } from "react";

export interface DepartmentLoad {
  dept: string;
  load: number;
  status: string;
}

export interface BedUnit {
  unit: string;
  total: number;
  occupied: number;
  cleaning: number;
  available: number;
}

export interface TelemetryData {
  timestamp: string;
  active_census: number;
  total_capacity: number;
  system_latency_ms: number;
  ai_nodes_active: number;
  ed_boarding: number;
  ed_avg_wait_min: number;
  pending_discharges: number;
  confirmed_discharges: number;
  surge_prediction_pct: number;
  department_loads: DepartmentLoad[];
  bed_units: BedUnit[];
}

export type ConnectionStatus = "connecting" | "connected" | "disconnected" | "error";

const MAX_RECONNECT_DELAY = 30000;
const INITIAL_RECONNECT_DELAY = 1000;

export function useTelemetry() {
  const [data, setData] = useState<TelemetryData | null>(null);
  const [status, setStatus] = useState<ConnectionStatus>("connecting");
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectAttempt = useRef(0);
  const reconnectTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  const connect = useCallback(() => {
    // Build WebSocket URL from API base
    const apiBase = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";
    const wsUrl = apiBase.replace(/^http/, "ws") + "/telemetry/stream";

    setStatus("connecting");

    try {
      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = () => {
        setStatus("connected");
        reconnectAttempt.current = 0; // Reset on successful connection
      };

      ws.onmessage = (event) => {
        try {
          const parsed: TelemetryData = JSON.parse(event.data);
          setData(parsed);
        } catch {
          console.error("[Telemetry] Failed to parse message");
        }
      };

      ws.onerror = () => {
        setStatus("error");
      };

      ws.onclose = () => {
        setStatus("disconnected");
        wsRef.current = null;

        // Exponential backoff reconnect
        const delay = Math.min(
          INITIAL_RECONNECT_DELAY * Math.pow(2, reconnectAttempt.current),
          MAX_RECONNECT_DELAY
        );
        reconnectAttempt.current += 1;

        reconnectTimer.current = setTimeout(() => {
          connect();
        }, delay);
      };
    } catch {
      setStatus("error");
    }
  }, []);

  useEffect(() => {
    connect();

    return () => {
      // Clean up on unmount
      if (reconnectTimer.current) {
        clearTimeout(reconnectTimer.current);
      }
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [connect]);

  return { data, status };
}
