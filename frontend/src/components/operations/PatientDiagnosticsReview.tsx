
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
    return "border-[var(--warning-border)] bg-[var(--warning-muted)] text-[var(--warning)]";
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
    <section className="panel overflow-hidden" role="region" aria-label="Diagnostic result review">
      <div className="panel-header flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between bg-[rgba(15,15,17,0.5)]">
        <div>
          <div className="section-label mb-1.5 flex items-center gap-1.5 text-[var(--accent)]">
            <ClipboardCheck size={13} aria-hidden="true" /> Diagnostics Review
          </div>
          <h2 className="text-sm font-bold text-[var(--text-primary)] uppercase">Pending Diagnostic Review</h2>
          <p className="mt-1 text-xs text-[var(--text-secondary)] uppercase">
            {safetyNote}
          </p>
        </div>
        <button
          type="button"
          onClick={() => void loadResults(true)}
          disabled={refreshing}
          className="btn btn-secondary text-xs flex items-center justify-center gap-1 cursor-pointer"
          aria-label="Refresh diagnostic results"
        >
          <RefreshCcw size={13} className={refreshing ? "animate-spin" : ""} aria-hidden="true" />
          Sync Reports
        </button>
      </div>

      <div className="p-4 space-y-4">
        <div className="flex justify-between items-center text-[10px] font-mono uppercase text-[var(--text-dim)] pb-2 border-b border-[var(--border)]">
          <span>{pendingResults.length} pending review</span>
          <span>{results.length} total results</span>
        </div>

        {loading ? (
          <div className="p-3 text-xs font-mono text-[var(--text-dim)] uppercase tracking-wider">
            Loading reports...
          </div>
        ) : error ? (
          <div className="flex items-center gap-1.5 p-3 text-xs font-mono text-[var(--danger)]" role="alert">
            <AlertTriangle size={13} aria-hidden="true" /> {error}
          </div>
        ) : pendingResults.length === 0 ? (
          <div className="p-3 text-xs font-mono text-[var(--text-dim)] uppercase tracking-wide">
            No pending diagnostic reports.
          </div>
        ) : (
          <div className="space-y-4" aria-label="Pending diagnostic results">
            {pendingResults.map((result) => (
              <div key={result.id} className="grid gap-4 lg:grid-cols-[1.2fr_0.8fr] p-3 rounded border border-[var(--border)] bg-[rgba(255,255,255,0.01)] hover:border-[var(--border-focus)] transition-colors">
                <div className="min-w-0 space-y-2">
                  <div className="flex flex-wrap items-center gap-2">
                    <span className={`px-1.5 py-0.5 rounded-sm border text-[9px] uppercase font-bold font-mono tracking-wider ${resultFlagStyle(result)}`}>
                      {result.abnormal_flag ? "Abnormal" : "Normal"}
                    </span>
                    <span className="mono-meta">{formatResultType(result.result_type)}</span>
                    <span className="mono-meta">{result.status}</span>
                  </div>
                  <h3 className="text-xs font-bold text-[var(--text-primary)] uppercase">{result.title}</h3>
                  <p className="text-xs text-[var(--text-secondary)] font-mono uppercase leading-relaxed">{result.summary}</p>
                </div>

                <div className="flex flex-col gap-2 bg-[rgba(255,255,255,0.015)] p-3 border border-[var(--border)] rounded">
                  <label className="text-[10px] font-bold uppercase tracking-wider text-[var(--text-secondary)]" htmlFor={`diagnostic-review-note-${result.id}`}>
                    Clinical Review Notes
                  </label>
                  <textarea
                    id={`diagnostic-review-note-${result.id}`}
                    aria-label={`Review note for ${result.title}`}
                    value={reviewNotes[result.id] ?? ""}
                    onChange={(event) => setReviewNotes((current) => ({ ...current, [result.id]: event.target.value }))}
                    rows={2}
                    className="w-full resize-none rounded border border-[var(--border)] bg-[#09090b] px-3.5 py-2 text-xs text-[var(--text-primary)] font-mono uppercase outline-none focus:border-[var(--accent)] transition-colors"
                    placeholder="Document clinical assessment context..."
                  />
                  <button
                    type="button"
                    onClick={() => void handleReview(result)}
                    disabled={reviewingResultId === result.id}
                    className="btn btn-primary text-xs py-1.5 flex items-center justify-center gap-1.5 cursor-pointer w-full"
                    aria-label={`Mark ${result.title} as reviewed`}
                  >
                    <CheckCircle2 size={13} aria-hidden="true" />
                    {reviewingResultId === result.id ? "Submitting..." : "Sign-Off Report"}
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </section>
  );
}
