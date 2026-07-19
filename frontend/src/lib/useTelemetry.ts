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
  const pollingInterval = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    let shouldReconnect = true;

    let apiBase = import.meta.env.NEXT_PUBLIC_API_URL || import.meta.env.VITE_PUBLIC_API_URL;
    if (!apiBase && typeof window !== "undefined") {
      if (window.location.port === "3000") {
        apiBase = "http://127.0.0.1:8000";
      } else {
        apiBase = window.location.origin;
      }
    }
    if (!apiBase) {
      apiBase = "http://127.0.0.1:8000";
    }
    const cleanApiBase = apiBase.replace(/\/$/, "");
    const token = useAuthStore.getState().token;

    async function fetchSnapshot() {
      try {
        const headers: Record<string, string> = {
          "Content-Type": "application/json",
        };
        if (token) {
          headers["Authorization"] = `Bearer ${token}`;
        }
        const response = await fetch(`${cleanApiBase}/v1/telemetry/snapshot`, { headers });
        if (response.ok) {
          const parsed: TelemetryData = await response.json();
          setData(parsed);
          setStatus("connected");
        } else {
          setStatus("error");
        }
      } catch {
        setStatus("error");
      }
    }

    function startPolling() {
      if (pollingInterval.current) return;
      fetchSnapshot();
      pollingInterval.current = setInterval(fetchSnapshot, 4000);
    }

    function stopPolling() {
      if (pollingInterval.current) {
        clearInterval(pollingInterval.current);
        pollingInterval.current = null;
      }
    }

    function connect() {
      if (!shouldReconnect) {
        return;
      }

      // Fallback to HTTP polling if we reach max reconnect attempts to keep UI responsive
      if (reconnectAttempt.current >= MAX_RECONNECT_ATTEMPTS) {
        startPolling();
        return;
      }

      const wsUrl = cleanApiBase.replace(/^http/, "ws") + `/telemetry/stream${token ? `?token=${token}` : ""}`;

      setStatus("connecting");

      try {
        const ws = new WebSocket(wsUrl);
        wsRef.current = ws;

        ws.onopen = () => {
          setStatus("connected");
          reconnectAttempt.current = 0;
          stopPolling();
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
          wsRef.current = null;

          if (!shouldReconnect) {
            return;
          }

          // Fallback to HTTP polling if we reached the limit
          if (reconnectAttempt.current >= MAX_RECONNECT_ATTEMPTS) {
            startPolling();
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
        startPolling();
      }
    }

    connect();

    return () => {
      shouldReconnect = false;
      stopPolling();

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
