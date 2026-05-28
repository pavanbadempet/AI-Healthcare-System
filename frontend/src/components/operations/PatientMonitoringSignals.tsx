"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { AlertTriangle, CheckCircle2, HeartPulse, RefreshCcw } from "lucide-react";
import { useAuthStore } from "@/lib/auth";
import {
  getDoctorPatientMonitoringSignals,
  resolveMonitoringSignal,
  type MonitoringSignal,
} from "@/lib/api";
import { notifyPatientCareEventsUpdated } from "@/lib/patientCareEvents";

interface PatientMonitoringSignalsProps {
  patientId: number;
  refreshIntervalMs?: number;
}

const severityClass: Record<string, string> = {
  critical: "border-[var(--danger-border)] bg-[var(--danger-muted)] text-[var(--danger)]",
  warning: "border-[var(--warning)]/30 bg-[var(--warning-muted)] text-[var(--warning)]",
  info: "border-[var(--accent-border)] bg-[var(--accent-muted)] text-[var(--accent)]",
};

function severityStyle(severity: string) {
  return severityClass[severity.toLowerCase()] ?? severityClass.info;
}

function formatSignalType(signalType: string) {
  return signalType
    .split("_")
    .filter(Boolean)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1).toLowerCase())
    .join(" ");
}

export default function PatientMonitoringSignals({
  patientId,
  refreshIntervalMs = 30000,
}: PatientMonitoringSignalsProps) {
  const { user } = useAuthStore();
  const [signals, setSignals] = useState<MonitoringSignal[]>([]);
  const [latestVitalCount, setLatestVitalCount] = useState(0);
  const [safetyNote, setSafetyNote] = useState("Signals highlight patterns for clinician review and are not diagnoses.");
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [resolvingSignalId, setResolvingSignalId] = useState<number | null>(null);
  const [error, setError] = useState("");

  const canReviewSignals = user?.role === "doctor";

  const sortedSignals = useMemo(
    () => [...signals].sort((a, b) => {
      const severityRank: Record<string, number> = { critical: 0, warning: 1, info: 2 };
      const rankDelta = (severityRank[a.severity.toLowerCase()] ?? 3) - (severityRank[b.severity.toLowerCase()] ?? 3);
      if (rankDelta !== 0) return rankDelta;
      return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
    }),
    [signals]
  );

  const loadSignals = useCallback(async (isManualRefresh = false) => {
    if (!canReviewSignals) {
      setLoading(false);
      return;
    }

    if (isManualRefresh) {
      setRefreshing(true);
    } else {
      setLoading(true);
    }
    setError("");

    try {
      const feed = await getDoctorPatientMonitoringSignals(patientId);
      setSignals(feed.open_signals);
      setLatestVitalCount(feed.latest_vitals.length);
      setSafetyNote(feed.clinical_safety_note ?? "Signals highlight patterns for clinician review and are not diagnoses.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load monitoring signals");
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [canReviewSignals, patientId]);

  useEffect(() => {
    void loadSignals();
    if (!canReviewSignals || refreshIntervalMs <= 0) return;

    const timer = window.setInterval(() => {
      void loadSignals(true);
    }, refreshIntervalMs);

    return () => window.clearInterval(timer);
  }, [canReviewSignals, loadSignals, refreshIntervalMs]);

  async function handleResolve(signal: MonitoringSignal) {
    setResolvingSignalId(signal.id);
    setError("");
    try {
      await resolveMonitoringSignal(signal.id);
      notifyPatientCareEventsUpdated(patientId);
      await loadSignals(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to resolve monitoring signal");
    } finally {
      setResolvingSignalId(null);
    }
  }

  if (!canReviewSignals) return null;

  return (
    <section className="panel p-5" role="region" aria-label="Monitoring signal review">
      <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
        <div>
          <div className="section-label mb-2 flex items-center gap-2">
            <HeartPulse size={14} aria-hidden="true" /> Monitoring Signals
          </div>
          <h2 className="text-xl font-semibold text-[var(--text-primary)]">Open Signal Review</h2>
          <p className="mt-1 max-w-3xl text-sm text-[var(--text-secondary)]">
            {safetyNote}
          </p>
        </div>
        <button
          type="button"
          onClick={() => void loadSignals(true)}
          disabled={refreshing}
          className="btn btn-secondary flex items-center justify-center gap-2 text-xs font-semibold uppercase tracking-wider"
          aria-label="Refresh monitoring signals"
        >
          <RefreshCcw size={14} className={refreshing ? "animate-spin" : ""} aria-hidden="true" />
          {refreshing ? "Refreshing" : "Refresh"}
        </button>
      </div>

      <div className="mt-4 rounded border border-[var(--border)] bg-[var(--bg-primary)]">
        <div className="flex flex-col gap-1 border-b border-[var(--border)] px-4 py-2 md:flex-row md:items-center md:justify-between">
          <span className="mono-meta">{sortedSignals.length} open signals</span>
          <span className="mono-meta">{latestVitalCount} recent observations</span>
        </div>

        {loading ? (
          <div className="p-5 text-sm text-[var(--text-secondary)]" role="status">
            Loading monitoring signals
          </div>
        ) : error ? (
          <div className="flex items-center gap-2 p-5 text-sm text-[var(--danger)]" role="alert">
            <AlertTriangle size={16} aria-hidden="true" /> {error}
          </div>
        ) : sortedSignals.length === 0 ? (
          <div className="p-5 text-sm text-[var(--text-secondary)]">
            No open monitoring signals.
          </div>
        ) : (
          <ul className="divide-y divide-[var(--border)]" aria-label="Open monitoring signals">
            {sortedSignals.map((signal) => (
              <li key={signal.id} className="flex flex-col gap-3 p-4 lg:flex-row lg:items-start lg:justify-between">
                <div className="min-w-0">
                  <div className="mb-2 flex flex-wrap items-center gap-2">
                    <span className={`rounded border px-2 py-1 text-[10px] uppercase tracking-widest ${severityStyle(signal.severity)}`}>
                      {signal.severity}
                    </span>
                    <span className="mono-meta">{formatSignalType(signal.signal_type)}</span>
                  </div>
                  <h3 className="text-sm font-semibold text-[var(--text-primary)]">{signal.title}</h3>
                  <p className="mt-1 text-sm text-[var(--text-secondary)]">{signal.summary}</p>
                </div>
                <button
                  type="button"
                  onClick={() => void handleResolve(signal)}
                  disabled={resolvingSignalId === signal.id}
                  className="btn btn-secondary flex shrink-0 items-center justify-center gap-2 text-xs font-semibold uppercase tracking-wider"
                  aria-label={`Resolve monitoring signal ${signal.title}`}
                >
                  <CheckCircle2 size={14} aria-hidden="true" />
                  {resolvingSignalId === signal.id ? "Resolving" : "Resolve"}
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>
    </section>
  );
}
