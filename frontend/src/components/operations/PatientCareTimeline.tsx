"use client";

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
  warning: "bg-[var(--warning-muted)] border-[var(--warning)]/30 text-[var(--warning)]",
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
      <section className="panel p-5" role="region" aria-label="Patient care timeline">
        <div className="flex items-start gap-3">
          <ShieldAlert size={18} className="text-[var(--text-dim)] mt-0.5" aria-hidden="true" />
          <div>
            <div className="section-label mb-2">Operational Timeline</div>
            <h2 className="text-lg font-semibold text-[var(--text-primary)]">Care timeline unavailable</h2>
            <p className="text-sm text-[var(--text-secondary)] mt-1">
              Timeline access is limited to assigned clinicians, admins, or the patient account.
            </p>
          </div>
        </div>
      </section>
    );
  }

  return (
    <section className="panel p-5" role="region" aria-label="Patient care timeline">
      <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
        <div>
          <div className="section-label mb-2 flex items-center gap-2">
            <Activity size={14} aria-hidden="true" /> Operational Feed
          </div>
          <h2 className="text-xl font-semibold text-[var(--text-primary)]">Live Care Timeline</h2>
          <p className="text-sm text-[var(--text-secondary)] mt-1 max-w-3xl">
            Role-scoped care events from encounters, orders, diagnostics, pharmacy, nursing, discharge, and interoperability workflows.
          </p>
        </div>
        <button
          type="button"
          onClick={() => void loadTimeline(true)}
          disabled={refreshing}
          className="btn btn-secondary text-xs font-semibold uppercase tracking-wider flex items-center justify-center gap-2"
          aria-label="Refresh timeline"
        >
          <RefreshCcw size={14} className={refreshing ? "animate-spin" : ""} aria-hidden="true" />
          {refreshing ? "Refreshing" : "Refresh"}
        </button>
      </div>

      <div className="mt-4 border border-[var(--border)] bg-[var(--bg-primary)] rounded overflow-hidden">
        <div className="px-4 py-2 border-b border-[var(--border)] flex flex-col gap-1 md:flex-row md:items-center md:justify-between">
          <p className="text-xs text-[var(--warning)]">{safetyNote}</p>
          <span className="mono-meta">
            {nextAfterId ? `Synced through event #${nextAfterId}` : "Awaiting event sync"}
          </span>
        </div>

        {loading ? (
          <div className="p-5 text-sm text-[var(--text-secondary)]" role="status">
            Loading care timeline
          </div>
        ) : error ? (
          <div className="p-5 text-sm text-[var(--danger)] flex items-center gap-2" role="alert">
            <AlertTriangle size={16} aria-hidden="true" /> {error}
          </div>
        ) : sortedEvents.length === 0 ? (
          <div className="p-5 text-sm text-[var(--text-secondary)]">
            No care events have been recorded for this patient yet.
          </div>
        ) : (
          <ol className="divide-y divide-[var(--border)]" aria-label="Timeline events">
            {sortedEvents.map((event) => (
              <li key={event.id} className="p-4 flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
                <div className="min-w-0">
                  <div className="flex flex-wrap items-center gap-2 mb-2">
                    <span className={`text-[10px] uppercase tracking-widest border px-2 py-1 rounded ${severityStyle(event.severity)}`}>
                      {event.severity}
                    </span>
                    <span className="mono-meta">{formatEventType(event.event_type)}</span>
                  </div>
                  <h3 className="text-sm font-semibold text-[var(--text-primary)]">{event.title}</h3>
                  {event.summary && (
                    <p className="text-sm text-[var(--text-secondary)] mt-1">{event.summary}</p>
                  )}
                </div>
                <div className="flex items-center gap-2 text-xs text-[var(--text-dim)] font-mono shrink-0">
                  <Clock3 size={13} aria-hidden="true" /> {formatEventTime(event.created_at)}
                </div>
              </li>
            ))}
          </ol>
        )}
      </div>
    </section>
  );
}
