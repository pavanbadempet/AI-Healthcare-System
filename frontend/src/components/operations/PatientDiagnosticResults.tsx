
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
    return "border-[var(--warning-border)] bg-[var(--warning-muted)] text-[var(--warning)]";
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
    <section className="panel overflow-hidden" role="region" aria-label="Reviewed diagnostic results">
      <div className="panel-header flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between bg-[rgba(15,15,17,0.5)]">
        <div>
          <div className="section-label mb-1.5 flex items-center gap-1.5 text-[var(--accent)]">
            <FileText size={13} aria-hidden="true" /> Released Diagnostics
          </div>
          <h2 className="text-sm font-bold text-[var(--text-primary)] uppercase">Reviewed Lab Results</h2>
          <p className="mt-1 text-xs text-[var(--text-secondary)] uppercase">
            Clinician reviewed reports and final diagnostic determinations. Patients should consult a qualified clinician for diagnosis or treatment decisions; emergencies require immediate hospital or local emergency care.
          </p>
        </div>
        <button
          type="button"
          onClick={() => void loadResults(true)}
          disabled={refreshing}
          className="btn btn-secondary text-xs flex items-center justify-center gap-1 cursor-pointer"
          aria-label="Refresh reviewed diagnostic results"
        >
          <RefreshCcw size={13} className={refreshing ? "animate-spin" : ""} aria-hidden="true" />
          Sync Diagnostics
        </button>
      </div>

      <div className="p-4 space-y-3">
        <div className="flex justify-between items-center text-[10px] font-mono uppercase text-[var(--text-dim)] pb-2 border-b border-[var(--border)]">
          <span>{releasedResults.length} reports released</span>
          <span>Observation list</span>
        </div>

        {loading ? (
          <div className="p-4 text-xs font-mono text-[var(--text-dim)] uppercase tracking-wider">
            Syncing results...
          </div>
        ) : error ? (
          <div className="flex items-center gap-1.5 p-4 text-xs font-mono text-[var(--danger)]" role="alert">
            <AlertTriangle size={13} aria-hidden="true" /> {error}
          </div>
        ) : releasedResults.length === 0 ? (
          <div className="p-4 text-xs font-mono text-[var(--text-dim)] uppercase tracking-wide">
            No active records found.
          </div>
        ) : (
          <ul className="divide-y divide-[var(--border-subtle)]" aria-label="Reviewed diagnostic result list">
            {releasedResults.map((result) => (
              <div key={result.id} className="py-3 first:pt-0 last:pb-0">
                <div className="mb-2 flex flex-wrap items-center gap-2">
                  <span className={`px-1.5 py-0.5 rounded-sm border text-[9px] uppercase font-bold font-mono tracking-wider ${resultStatusStyle(result)}`}>
                    {formatReviewStatus(result.review_status)}
                  </span>
                  <span className="mono-meta">{formatResultType(result.result_type)}</span>
                  <span className="mono-meta">{result.abnormal_flag ? "Abnormal" : "Normal"}</span>
                </div>
                <h3 className="text-xs font-bold text-[var(--text-primary)] uppercase">{result.title}</h3>
                <p className="mt-1 text-xs text-[var(--text-secondary)] font-mono uppercase leading-relaxed">{result.summary}</p>
                {result.review_note && (
                  <p className="mt-2.5 rounded border border-[var(--border)] bg-[rgba(255,255,255,0.015)] px-3 py-2 text-xs font-mono text-[var(--text-secondary)] uppercase">
                    Review Context: {result.review_note}
                  </p>
                )}
              </div>
            ))}
          </ul>
        )}
      </div>
    </section>
  );
}
