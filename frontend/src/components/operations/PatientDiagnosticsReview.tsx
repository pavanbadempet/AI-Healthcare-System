"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { AlertTriangle, CheckCircle2, ClipboardCheck, RefreshCcw } from "lucide-react";
import { useAuthStore } from "@/lib/auth";
import {
  getDoctorPatientDiagnosticResults,
  reviewDiagnosticResult,
  type DiagnosticResult,
} from "@/lib/api";
import { notifyPatientCareEventsUpdated } from "@/lib/patientCareEvents";

interface PatientDiagnosticsReviewProps {
  patientId: number;
  refreshIntervalMs?: number;
}

const DEFAULT_SAFETY_NOTE = "Diagnostic results require clinician review and are not AI diagnoses.";

function formatResultType(resultType: string) {
  return resultType
    .split("_")
    .filter(Boolean)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1).toLowerCase())
    .join(" ");
}

function resultFlagStyle(result: DiagnosticResult) {
  if (result.abnormal_flag) {
    return "border-[var(--warning)]/30 bg-[var(--warning-muted)] text-[var(--warning)]";
  }
  return "border-[var(--success-border)] bg-[var(--success-muted)] text-[var(--success)]";
}

export default function PatientDiagnosticsReview({
  patientId,
  refreshIntervalMs = 30000,
}: PatientDiagnosticsReviewProps) {
  const { user } = useAuthStore();
  const [results, setResults] = useState<DiagnosticResult[]>([]);
  const [safetyNote, setSafetyNote] = useState(DEFAULT_SAFETY_NOTE);
  const [reviewNotes, setReviewNotes] = useState<Record<number, string>>({});
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [reviewingResultId, setReviewingResultId] = useState<number | null>(null);
  const [error, setError] = useState("");

  const canReviewDiagnostics = user?.role === "doctor";

  const pendingResults = useMemo(
    () => results
      .filter((result) => result.review_status === "pending_review")
      .sort((a, b) => {
        if (a.abnormal_flag !== b.abnormal_flag) return a.abnormal_flag ? -1 : 1;
        return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
      }),
    [results]
  );

  const loadResults = useCallback(async (isManualRefresh = false) => {
    if (!canReviewDiagnostics) {
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
      const feed = await getDoctorPatientDiagnosticResults(patientId);
      setResults(feed.results);
      setSafetyNote(feed.clinical_safety_note ?? DEFAULT_SAFETY_NOTE);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load diagnostic results");
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [canReviewDiagnostics, patientId]);

  useEffect(() => {
    void loadResults();
    if (!canReviewDiagnostics || refreshIntervalMs <= 0) return;

    const timer = window.setInterval(() => {
      void loadResults(true);
    }, refreshIntervalMs);

    return () => window.clearInterval(timer);
  }, [canReviewDiagnostics, loadResults, refreshIntervalMs]);

  async function handleReview(result: DiagnosticResult) {
    setReviewingResultId(result.id);
    setError("");
    try {
      await reviewDiagnosticResult(result.id, {
        review_status: "reviewed",
        review_note: reviewNotes[result.id]?.trim() || undefined,
      });
      setReviewNotes((current) => {
        const next = { ...current };
        delete next[result.id];
        return next;
      });
      notifyPatientCareEventsUpdated(patientId);
      await loadResults(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to review diagnostic result");
    } finally {
      setReviewingResultId(null);
    }
  }

  if (!canReviewDiagnostics) return null;

  return (
    <section className="panel p-5" role="region" aria-label="Diagnostic result review">
      <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
        <div>
          <div className="section-label mb-2 flex items-center gap-2">
            <ClipboardCheck size={14} aria-hidden="true" /> Diagnostics
          </div>
          <h2 className="text-xl font-semibold text-[var(--text-primary)]">Pending Diagnostic Review</h2>
          <p className="mt-1 max-w-3xl text-sm text-[var(--text-secondary)]">
            {safetyNote}
          </p>
        </div>
        <button
          type="button"
          onClick={() => void loadResults(true)}
          disabled={refreshing}
          className="btn btn-secondary flex items-center justify-center gap-2 text-xs font-semibold uppercase tracking-wider"
          aria-label="Refresh diagnostic results"
        >
          <RefreshCcw size={14} className={refreshing ? "animate-spin" : ""} aria-hidden="true" />
          {refreshing ? "Refreshing" : "Refresh"}
        </button>
      </div>

      <div className="mt-4 rounded border border-[var(--border)] bg-[var(--bg-primary)]">
        <div className="flex flex-col gap-1 border-b border-[var(--border)] px-4 py-2 md:flex-row md:items-center md:justify-between">
          <span className="mono-meta">{pendingResults.length} pending results</span>
          <span className="mono-meta">{results.length} total diagnostic results</span>
        </div>

        {loading ? (
          <div className="p-5 text-sm text-[var(--text-secondary)]" role="status">
            Loading diagnostic results
          </div>
        ) : error ? (
          <div className="flex items-center gap-2 p-5 text-sm text-[var(--danger)]" role="alert">
            <AlertTriangle size={16} aria-hidden="true" /> {error}
          </div>
        ) : pendingResults.length === 0 ? (
          <div className="p-5 text-sm text-[var(--text-secondary)]">
            No pending diagnostic results.
          </div>
        ) : (
          <ul className="divide-y divide-[var(--border)]" aria-label="Pending diagnostic results">
            {pendingResults.map((result) => (
              <li key={result.id} className="grid gap-4 p-4 lg:grid-cols-[minmax(0,1fr)_minmax(280px,360px)]">
                <div className="min-w-0">
                  <div className="mb-2 flex flex-wrap items-center gap-2">
                    <span className={`rounded border px-2 py-1 text-[10px] uppercase tracking-widest ${resultFlagStyle(result)}`}>
                      {result.abnormal_flag ? "Abnormal" : "Normal"}
                    </span>
                    <span className="mono-meta">{formatResultType(result.result_type)}</span>
                    <span className="mono-meta">{result.status}</span>
                  </div>
                  <h3 className="text-sm font-semibold text-[var(--text-primary)]">{result.title}</h3>
                  <p className="mt-1 text-sm text-[var(--text-secondary)]">{result.summary}</p>
                </div>

                <div className="flex min-w-0 flex-col gap-3">
                  <label className="text-xs font-semibold uppercase tracking-wider text-[var(--text-secondary)]" htmlFor={`diagnostic-review-note-${result.id}`}>
                    Review note
                  </label>
                  <textarea
                    id={`diagnostic-review-note-${result.id}`}
                    aria-label={`Review note for ${result.title}`}
                    value={reviewNotes[result.id] ?? ""}
                    onChange={(event) => setReviewNotes((current) => ({ ...current, [result.id]: event.target.value }))}
                    rows={3}
                    className="min-h-[84px] w-full resize-y rounded border border-[var(--border)] bg-[var(--bg-secondary)] px-3 py-2 text-sm text-[var(--text-primary)] outline-none focus:border-[var(--accent)]"
                    placeholder="Document clinician review context"
                  />
                  <button
                    type="button"
                    onClick={() => void handleReview(result)}
                    disabled={reviewingResultId === result.id}
                    className="btn btn-secondary flex items-center justify-center gap-2 text-xs font-semibold uppercase tracking-wider"
                    aria-label={`Mark ${result.title} as reviewed`}
                  >
                    <CheckCircle2 size={14} aria-hidden="true" />
                    {reviewingResultId === result.id ? "Reviewing" : "Mark Reviewed"}
                  </button>
                </div>
              </li>
            ))}
          </ul>
        )}
      </div>
    </section>
  );
}
