
import { useCallback, useEffect, useMemo, useState } from "react";
import { Activity, AlertTriangle, Clock3, RefreshCcw, ShieldAlert } from "lucide-react";
import { useAuthStore } from "@/lib/auth";
import {
  getAdminPatientCareEventFeed,
  getDoctorPatientCareEventFeed,
  getPatientCareEventFeed,
  type CareEvent,
} from "@/lib/api";
import {
  PATIENT_CARE_EVENTS_UPDATED,
  patientCareEventMatches,
} from "@/lib/patientCareEvents";

const staffRoles = new Set(["doctor", "admin"]);
const defaultSafetyNote = "Care events are operational records for review and do not replace clinician judgment.";

const severityClass: Record<string, string> = {
  critical: "bg-[var(--danger-muted)] border-[var(--danger-border)] text-[var(--danger)]",
  warning: "bg-[var(--warning-muted)] border-[var(--warning-border)] text-[var(--warning)]",
  info: "bg-[var(--accent-muted)] border-[var(--accent-border)] text-[var(--accent)]",
  success: "bg-[var(--success-muted)] border-[var(--success-border)] text-[var(--success)]",
};

interface PatientCareTimelineProps {
  patientId: number;
  limit?: number;
  refreshIntervalMs?: number;
}

function formatEventType(eventType: string) {
  return eventType
    .split("_")
    .filter(Boolean)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1).toLowerCase())
    .join(" ");
}

function formatEventTime(value: string) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return new Intl.DateTimeFormat(undefined, {
    month: "short",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  }).format(date);
}

function severityStyle(severity: string) {
  return severityClass[severity.toLowerCase()] ?? severityClass.info;
}

export default function PatientCareTimeline({
  patientId,
  limit = 25,
  refreshIntervalMs = 30000,
}: PatientCareTimelineProps) {
  const { user } = useAuthStore();
  const [events, setEvents] = useState<CareEvent[]>([]);
  const [nextAfterId, setNextAfterId] = useState<number | null>(null);
  const [safetyNote, setSafetyNote] = useState(defaultSafetyNote);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState("");

  const role = user?.role ?? "";
  const canViewAsAdmin = role === "admin";
  const canViewAsStaff = staffRoles.has(role);
  const canViewAsPatient = role === "patient" && user?.id === patientId;
  const canViewTimeline = canViewAsStaff || canViewAsPatient;

  const loadTimeline = useCallback(async (isManualRefresh = false) => {
    if (!canViewTimeline) {
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
      const feed = canViewAsPatient
        ? await getPatientCareEventFeed(limit)
        : canViewAsAdmin
          ? await getAdminPatientCareEventFeed(patientId, limit)
        : await getDoctorPatientCareEventFeed(patientId, limit);
      setEvents(feed.events);
      setNextAfterId(feed.next_after_id ?? null);
      setSafetyNote(feed.clinical_safety_note ?? defaultSafetyNote);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load care timeline");
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [canViewAsAdmin, canViewAsPatient, canViewTimeline, limit, patientId]);

  useEffect(() => {
    void loadTimeline();
    if (!canViewTimeline || refreshIntervalMs <= 0) return;

    const timer = window.setInterval(() => {
      void loadTimeline(true);
    }, refreshIntervalMs);

    return () => window.clearInterval(timer);
  }, [canViewTimeline, loadTimeline, refreshIntervalMs]);

  useEffect(() => {
    if (!canViewTimeline) return;

    const handleCareEventUpdate = (event: Event) => {
      if (!patientCareEventMatches(event, patientId)) return;
      void loadTimeline(true);
    };

    window.addEventListener(PATIENT_CARE_EVENTS_UPDATED, handleCareEventUpdate);
    return () => window.removeEventListener(PATIENT_CARE_EVENTS_UPDATED, handleCareEventUpdate);
  }, [canViewTimeline, loadTimeline, patientId]);

  const sortedEvents = useMemo(
    () => [...events].sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime()),
    [events]
  );

  if (!canViewTimeline) {
    return (
      <section className="panel p-4" role="region" aria-label="Patient care timeline">
        <div className="flex items-start gap-3">
          <ShieldAlert size={16} className="text-[var(--text-dim)] mt-0.5" aria-hidden="true" />
          <div>
            <div className="section-label mb-1">Operational Timeline</div>
            <h2 className="text-sm font-bold text-[var(--text-primary)] uppercase">Care timeline unavailable</h2>
            <p className="text-xs text-[var(--text-secondary)] mt-1 uppercase font-mono">
              Timeline access is limited to authorized clinicial operators.
            </p>
          </div>
        </div>
      </section>
    );
  }

  return (
    <section className="panel overflow-hidden" role="region" aria-label="Patient care timeline">
      <div className="panel-header flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between bg-[rgba(15,15,17,0.5)]">
        <div>
          <div className="section-label mb-1.5 flex items-center gap-1.5 text-[var(--accent)]">
            <Activity size={13} aria-hidden="true" /> Operational Activity Logs
          </div>
          <h2 className="text-sm font-bold text-[var(--text-primary)] uppercase">Live Care Timeline</h2>
          <p className="text-xs text-[var(--text-secondary)] mt-1 uppercase">
            Aggregated operational feeds from admissions, order logs, diagnostics, and integrations.
          </p>
        </div>
        <button
          type="button"
          onClick={() => void loadTimeline(true)}
          disabled={refreshing}
          className="btn btn-secondary text-xs flex items-center justify-center gap-1 cursor-pointer"
          aria-label="Refresh timeline"
        >
          <RefreshCcw size={13} className={refreshing ? "animate-spin" : ""} aria-hidden="true" />
          Sync Feed
        </button>
      </div>

      <div className="p-4 space-y-4">
        <div className="flex flex-col gap-1 md:flex-row md:items-center md:justify-between pb-2 border-b border-[var(--border)] text-[10px] font-mono uppercase text-[var(--text-dim)]">
          <p className="text-[var(--warning)]">{safetyNote}</p>
          <span>
            {nextAfterId ? `Synced Event ID: #${nextAfterId}` : "Awaiting event feed..."}
          </span>
        </div>

        {loading ? (
          <div className="p-3 text-xs font-mono text-[var(--text-dim)] uppercase tracking-wider">
            Loading timeline...
          </div>
        ) : error ? (
          <div className="p-3 text-xs font-mono text-[var(--danger)] flex items-center gap-1.5" role="alert">
            <AlertTriangle size={13} aria-hidden="true" /> {error}
          </div>
        ) : sortedEvents.length === 0 ? (
          <div className="p-3 text-xs font-mono text-[var(--text-dim)] uppercase tracking-wide">
            No care events recorded.
          </div>
        ) : (
          <div className="space-y-2.5" aria-label="Timeline events">
            {sortedEvents.map((event) => (
              <div key={event.id} className="p-3 rounded border border-[var(--border)] bg-[rgba(255,255,255,0.01)] hover:border-[var(--border-focus)] transition-colors flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
                <div className="min-w-0 space-y-1.5">
                  <div className="flex flex-wrap items-center gap-2">
                    <span className={`px-1.5 py-0.5 rounded-sm border text-[9px] uppercase font-bold font-mono tracking-wider ${severityStyle(event.severity)}`}>
                      {event.severity}
                    </span>
                    <span className="mono-meta">{formatEventType(event.event_type)}</span>
                  </div>
                  <h3 className="text-xs font-bold text-[var(--text-primary)] uppercase">{event.title}</h3>
                  {event.summary && (
                    <p className="text-xs text-[var(--text-secondary)] font-mono uppercase mt-0.5 leading-relaxed">{event.summary}</p>
                  )}
                </div>
                <div className="flex items-center gap-1.5 text-[10px] text-[var(--text-dim)] font-mono uppercase shrink-0">
                  <Clock3 size={12} aria-hidden="true" /> {formatEventTime(event.created_at)}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </section>
  );
}
