"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { AlertTriangle, FileText, RefreshCcw } from "lucide-react";
import { useAuthStore } from "@/lib/auth";
import {
  getPatientDiagnosticResults,
  type DiagnosticResult,
} from "@/lib/api";

interface PatientDiagnosticResultsProps {
  patientId: number;
  refreshIntervalMs?: number;
}

const visibleReviewStatuses = new Set(["reviewed", "needs_follow_up"]);

function formatResultType(resultType: string) {
  return resultType
    .split("_")
    .filter(Boolean)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1).toLowerCase())
    .join(" ");
}

function formatReviewStatus(status: string) {
  return status
    .split("_")
    .filter(Boolean)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1).toLowerCase())
    .join(" ");
}

function resultStatusStyle(result: DiagnosticResult) {
  if (result.review_status === "needs_follow_up") {
    return "border-[var(--warning)]/30 bg-[var(--warning-muted)] text-[var(--warning)]";
  }
  if (result.abnormal_flag) {
    return "border-[var(--danger-border)] bg-[var(--danger-muted)] text-[var(--danger)]";
  }
  return "border-[var(--success-border)] bg-[var(--success-muted)] text-[var(--success)]";
}

export default function PatientDiagnosticResults({
  patientId,
  refreshIntervalMs = 30000,
}: PatientDiagnosticResultsProps) {
  const { user } = useAuthStore();
  const [results, setResults] = useState<DiagnosticResult[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState("");

  const canViewPatientResults = user?.role === "patient" && user.id === patientId;

  const releasedResults = useMemo(
    () => results
      .filter((result) => visibleReviewStatuses.has(result.review_status))
      .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime()),
    [results]
  );

  const loadResults = useCallback(async (isManualRefresh = false) => {
    if (!canViewPatientResults) {
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
      const patientResults = await getPatientDiagnosticResults();
      setResults(patientResults);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load diagnostic results");
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [canViewPatientResults]);

  useEffect(() => {
    void loadResults();
    if (!canViewPatientResults || refreshIntervalMs <= 0) return;

    const timer = window.setInterval(() => {
      void loadResults(true);
    }, refreshIntervalMs);

    return () => window.clearInterval(timer);
  }, [canViewPatientResults, loadResults, refreshIntervalMs]);

  if (!canViewPatientResults) return null;

  return (
    <section className="panel p-5" role="region" aria-label="Reviewed diagnostic results">
      <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
        <div>
          <div className="section-label mb-2 flex items-center gap-2">
            <FileText size={14} aria-hidden="true" /> Released Diagnostics
          </div>
          <h2 className="text-xl font-semibold text-[var(--text-primary)]">Reviewed Diagnostic Results</h2>
          <p className="mt-1 max-w-3xl text-sm text-[var(--text-secondary)]">
            These results have been released after clinician review. Patients should consult a qualified clinician for diagnosis or treatment decisions; emergencies require immediate hospital or local emergency care.
          </p>
        </div>
        <button
          type="button"
          onClick={() => void loadResults(true)}
          disabled={refreshing}
          className="btn btn-secondary flex items-center justify-center gap-2 text-xs font-semibold uppercase tracking-wider"
          aria-label="Refresh reviewed diagnostic results"
        >
          <RefreshCcw size={14} className={refreshing ? "animate-spin" : ""} aria-hidden="true" />
          {refreshing ? "Refreshing" : "Refresh"}
        </button>
      </div>

      <div className="mt-4 rounded border border-[var(--border)] bg-[var(--bg-primary)]">
        <div className="flex flex-col gap-1 border-b border-[var(--border)] px-4 py-2 md:flex-row md:items-center md:justify-between">
          <span className="mono-meta">{releasedResults.length} released results</span>
          <span className="mono-meta">Clinician reviewed</span>
        </div>

        {loading ? (
          <div className="p-5 text-sm text-[var(--text-secondary)]" role="status">
            Loading diagnostic results
          </div>
        ) : error ? (
          <div className="flex items-center gap-2 p-5 text-sm text-[var(--danger)]" role="alert">
            <AlertTriangle size={16} aria-hidden="true" /> {error}
          </div>
        ) : releasedResults.length === 0 ? (
          <div className="p-5 text-sm text-[var(--text-secondary)]">
            No reviewed diagnostic results.
          </div>
        ) : (
          <ul className="divide-y divide-[var(--border)]" aria-label="Reviewed diagnostic result list">
            {releasedResults.map((result) => (
              <li key={result.id} className="p-4">
                <div className="mb-2 flex flex-wrap items-center gap-2">
                  <span className={`rounded border px-2 py-1 text-[10px] uppercase tracking-widest ${resultStatusStyle(result)}`}>
                    {formatReviewStatus(result.review_status)}
                  </span>
                  <span className="mono-meta">{formatResultType(result.result_type)}</span>
                  <span className="mono-meta">{result.abnormal_flag ? "Abnormal" : "Normal"}</span>
                </div>
                <h3 className="text-sm font-semibold text-[var(--text-primary)]">{result.title}</h3>
                <p className="mt-1 text-sm text-[var(--text-secondary)]">{result.summary}</p>
                {result.review_note && (
                  <p className="mt-3 rounded border border-[var(--border)] bg-[var(--bg-secondary)] px-3 py-2 text-sm text-[var(--text-secondary)]">
                    {result.review_note}
                  </p>
                )}
              </li>
            ))}
          </ul>
        )}
      </div>
    </section>
  );
}
