/**
 * AI Healthcare System - Global Singleton Real-Time Telemetry Hook
 * 
 * Manages a single shared WebSocket telemetry stream and fallback HTTP poll
 * across all active application components to prevent network spam and UI freezing.
 */

import { useState, useEffect } from "react";
import { useAuthStore } from "./auth";
import { getWebSocketUrl } from "./apiCore";

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

// --- Global Singleton Module State ---
let sharedData: TelemetryData | null = null;
let sharedStatus: ConnectionStatus = "connecting";
const subscribers = new Set<(state: { data: TelemetryData | null; status: ConnectionStatus }) => void>();

let globalWs: WebSocket | null = null;
let globalPollingInterval: ReturnType<typeof setInterval> | null = null;
let reconnectTimer: ReturnType<typeof setTimeout> | null = null;
let reconnectAttempt = 0;
const MAX_RECONNECT_ATTEMPTS = 5;

const defaultDepartmentLoads: DepartmentLoad[] = [
  { dept: "Cardiology", load: 88, status: "Critical" },
  { dept: "Pulmonology", load: 64, status: "Stable" },
  { dept: "Nephrology", load: 42, status: "Optimal" },
  { dept: "Endocrinology", load: 76, status: "Elevated" },
];

const defaultBedUnits: BedUnit[] = [
  { unit: "ICU-A", total: 12, occupied: 11, cleaning: 1, available: 0 },
  { unit: "ICU-B", total: 12, occupied: 9, cleaning: 0, available: 3 },
  { unit: "Cardiac Care", total: 16, occupied: 14, cleaning: 1, available: 1 },
  { unit: "General Med", total: 32, occupied: 24, cleaning: 2, available: 6 },
  { unit: "Surgical Step", total: 20, occupied: 15, cleaning: 1, available: 4 },
  { unit: "Emergency Obs", total: 8, occupied: 6, cleaning: 0, available: 2 },
];

function normalizeTelemetry(raw: any): TelemetryData {
  if (!raw || typeof raw !== "object") {
    return {
      timestamp: new Date().toISOString(),
      active_census: 79,
      total_capacity: 100,
      system_latency_ms: 14,
      ai_nodes_active: 8,
      ed_boarding: 14,
      ed_avg_wait_min: 22,
      pending_discharges: 18,
      confirmed_discharges: 12,
      surge_prediction_pct: 34,
      department_loads: defaultDepartmentLoads,
      bed_units: defaultBedUnits,
    };
  }

  return {
    ...raw,
    timestamp: raw.snapshot_timestamp || raw.timestamp || new Date().toISOString(),
    active_census: raw.total_active_beds ?? raw.active_census ?? 79,
    total_capacity: raw.total_capacity ?? 100,
    system_latency_ms: raw.system_latency_ms ?? 14,
    ai_nodes_active: raw.ai_nodes_active ?? 8,
    ed_boarding: raw.ed_boarding ?? 14,
    ed_avg_wait_min: raw.ed_avg_wait_min ?? 22,
    pending_discharges: raw.pending_discharges ?? 18,
    confirmed_discharges: raw.confirmed_discharges ?? 12,
    surge_prediction_pct: raw.surge_prediction_pct ?? 34,
    department_loads: Array.isArray(raw.department_loads) && raw.department_loads.length > 0 ? raw.department_loads : defaultDepartmentLoads,
    bed_units: Array.isArray(raw.bed_units) && raw.bed_units.length > 0 ? raw.bed_units : defaultBedUnits,
  };
}

function notifySubscribers() {
  subscribers.forEach((cb) => cb({ data: sharedData, status: sharedStatus }));
}

function stopGlobalPolling() {
  if (globalPollingInterval) {
    clearInterval(globalPollingInterval);
    globalPollingInterval = null;
  }
}

async function fetchSnapshot() {
  try {
    let apiBase = import.meta.env.NEXT_PUBLIC_API_URL || import.meta.env.VITE_PUBLIC_API_URL;
    if (!apiBase && typeof window !== "undefined") {
      apiBase = window.location.port === "3000" ? "http://127.0.0.1:8000" : window.location.origin;
    }
    apiBase = (apiBase || "http://127.0.0.1:8000").replace(/\/$/, "");

    const token = useAuthStore.getState().token;
    const headers: Record<string, string> = { "Content-Type": "application/json" };
    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }

    const response = await fetch(`${apiBase}/v1/telemetry/snapshot`, { headers });
    if (response.ok) {
      const raw = await response.json();
      sharedData = normalizeTelemetry(raw);
      sharedStatus = "connected";
    } else {
      sharedStatus = "error";
    }
  } catch {
    sharedStatus = "error";
  }
  notifySubscribers();
}

function startGlobalPolling() {
  if (globalPollingInterval) return;
  fetchSnapshot();
  globalPollingInterval = setInterval(fetchSnapshot, 10000);
}

function connectGlobalWs() {
  if (subscribers.size === 0) return;

  if (reconnectAttempt >= MAX_RECONNECT_ATTEMPTS) {
    startGlobalPolling();
    return;
  }

  const token = useAuthStore.getState().token;
  const wsUrl = getWebSocketUrl("/v1/telemetry/stream") + (token ? `?token=${token}` : "");

  try {
    if (globalWs) {
      try { globalWs.close(); } catch {}
      globalWs = null;
    }

    const ws = new WebSocket(wsUrl);
    globalWs = ws;

    ws.onopen = () => {
      sharedStatus = "connected";
      reconnectAttempt = 0;
      stopGlobalPolling();
      notifySubscribers();
    };

    ws.onmessage = (event) => {
      try {
        const raw = JSON.parse(event.data);
        sharedData = normalizeTelemetry(raw);
        sharedStatus = "connected";
        notifySubscribers();
      } catch {
        console.error("[Telemetry] Failed to parse message");
      }
    };

    ws.onerror = () => {
      sharedStatus = "error";
      notifySubscribers();
    };

    ws.onclose = () => {
      globalWs = null;

      if (subscribers.size === 0) {
        stopGlobalPolling();
        return;
      }

      startGlobalPolling();

      const delay = Math.min(2000 * Math.pow(2, reconnectAttempt), 30000);
      reconnectAttempt += 1;

      if (reconnectTimer) clearTimeout(reconnectTimer);
      reconnectTimer = setTimeout(() => {
        if (subscribers.size > 0) {
          connectGlobalWs();
        }
      }, delay);
    };
  } catch {
    sharedStatus = "error";
    startGlobalPolling();
  }
}

export function useTelemetry() {
  const [state, setState] = useState({ data: sharedData, status: sharedStatus });

  useEffect(() => {
    subscribers.add(setState);

    if (subscribers.size === 1) {
      fetchSnapshot();
      connectGlobalWs();
    } else {
      setState({ data: sharedData, status: sharedStatus });
    }

    return () => {
      subscribers.delete(setState);
      if (subscribers.size === 0) {
        stopGlobalPolling();
        if (reconnectTimer) {
          clearTimeout(reconnectTimer);
          reconnectTimer = null;
        }
        if (globalWs) {
          try { globalWs.close(); } catch {}
          globalWs = null;
        }
      }
    };
  }, []);

  return state;
}
