/**
 * AI Healthcare System - Real-Time Telemetry Hook
 * 
 * Connects to the backend WebSocket telemetry stream and provides
 * live-updating hospital operations data to any component.
 * 
 * Features:
 * - Auto-reconnect with exponential backoff
 * - Connection state tracking
 * - Graceful cleanup on unmount
 */

import { useState, useEffect, useRef } from "react";
import { useAuthStore } from "./auth";

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
  spark_batch_id?: number;
  spark_records_processed?: number;
  spark_ml_latency_ms?: number;
  is_real_stream?: boolean;
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

const MAX_RECONNECT_DELAY = 60000;
const INITIAL_RECONNECT_DELAY = 2000;
const MAX_RECONNECT_ATTEMPTS = 5;

export function useTelemetry() {
  const [data, setData] = useState<TelemetryData | null>(null);
  const [status, setStatus] = useState<ConnectionStatus>("connecting");
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectAttempt = useRef(0);
  const reconnectTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    let shouldReconnect = true;

    function connect() {
      if (!shouldReconnect) {
        return;
      }

      // Give up after MAX_RECONNECT_ATTEMPTS to avoid hammering a non-existent endpoint
      if (reconnectAttempt.current >= MAX_RECONNECT_ATTEMPTS) {
        setStatus("disconnected");
        return;
      }

      const token = useAuthStore.getState().token;
      let apiBase = import.meta.env.NEXT_PUBLIC_API_URL || import.meta.env.VITE_PUBLIC_API_URL;
      if (!apiBase && typeof window !== "undefined") {
        apiBase = window.location.origin;
      }
      if (!apiBase) {
        apiBase = "http://127.0.0.1:8000";
      }
      const wsUrl = apiBase.replace(/^http/, "ws") + `/telemetry/stream${token ? `?token=${token}` : ""}`;

      setStatus("connecting");

      try {
        const ws = new WebSocket(wsUrl);
        wsRef.current = ws;

        ws.onopen = () => {
          setStatus("connected");
          reconnectAttempt.current = 0;
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

          if (!shouldReconnect) {
            return;
          }

          // Stop reconnecting after max attempts
          if (reconnectAttempt.current >= MAX_RECONNECT_ATTEMPTS) {
            return;
          }

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
    }

    connect();

    return () => {
      shouldReconnect = false;

      // Clean up on unmount
      if (reconnectTimer.current) {
        clearTimeout(reconnectTimer.current);
        reconnectTimer.current = null;
      }
      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
      }
    };
  }, []);

  return { data, status };
}
