
import { useCallback, useEffect, useMemo, useState } from "react";
import { AlertTriangle, Pill, RefreshCcw } from "lucide-react";
import { useAuthStore } from "@/lib/auth";
import {
  getDoctorPatientPrescriptions,
  getPatientPrescriptions,
  type Prescription,
  type PrescriptionItem,
} from "@/lib/api";

interface PatientMedicationsPanelProps {
  patientId: number;
  refreshIntervalMs?: number;
}

const DEFAULT_CLINICAL_NOTE = "Prescriptions support clinician and pharmacist workflows.";
const PATIENT_MEDICATION_NOTE = "Medication details are for review. Consult your provider before changes.";

function statusStyle(status: string) {
  const normalized = status.toLowerCase();
  if (normalized === "dispensed") {
    return "border-[var(--success-border)] bg-[var(--success-muted)] text-[var(--success)]";
  }
  if (normalized === "partially_dispensed") {
    return "border-[var(--warning-border)] bg-[var(--warning-muted)] text-[var(--warning)]";
  }
  return "border-[var(--accent-border)] bg-[var(--accent-muted)] text-[var(--accent)]";
}

function formatStatus(status: string) {
  return status
    .split("_")
    .filter(Boolean)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1).toLowerCase())
    .join(" ");
}

function itemQuantityText(item: PrescriptionItem) {
  return `${item.quantity_prescribed} units prescribed`;
}

function sortedPrescriptions(prescriptions: Prescription[]) {
  return [...prescriptions].sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime());
}

export default function PatientMedicationsPanel({
  patientId,
  refreshIntervalMs = 30000,
}: PatientMedicationsPanelProps) {
  const { user } = useAuthStore();
  const [prescriptions, setPrescriptions] = useState<Prescription[]>([]);
  const [safetyNote, setSafetyNote] = useState(DEFAULT_CLINICAL_NOTE);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState("");

  const canLoadPrescriptions = useMemo(() => {
    const role = user?.role || "";
    return role === "doctor" || (role === "patient" && user?.id === patientId);
  }, [user, patientId]);

  const orderedPrescriptions = useMemo(() => sortedPrescriptions(prescriptions), [prescriptions]);

  const loadPrescriptions = useCallback(async (isManualRefresh = false) => {
    if (!canLoadPrescriptions) {
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
      if (user?.role === "doctor") {
        const feed = await getDoctorPatientPrescriptions(patientId);
        setPrescriptions(feed.prescriptions);
        setSafetyNote(feed.clinical_safety_note ?? DEFAULT_CLINICAL_NOTE);
      } else {
        setPrescriptions(await getPatientPrescriptions());
        setSafetyNote(PATIENT_MEDICATION_NOTE);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load medication orders");
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [canLoadPrescriptions, user, patientId]);

  useEffect(() => {
    void loadPrescriptions();
    if (!canLoadPrescriptions || refreshIntervalMs <= 0) return;

    const timer = window.setInterval(() => {
      void loadPrescriptions(true);
    }, refreshIntervalMs);

    return () => window.clearInterval(timer);
  }, [canLoadPrescriptions, loadPrescriptions, refreshIntervalMs]);

  if (!canLoadPrescriptions) {
    return (
      <div className="panel p-4" role="region" aria-label="Active medications">
        <h3 className="section-label mb-3">Medication Orders</h3>
        <div className="rounded border border-[var(--border)] bg-[rgba(255,255,255,0.01)] p-3 text-xs font-mono text-[var(--text-secondary)] uppercase">
          No active medication records.
        </div>
      </div>
    );
  }

  return (
    <section className="panel overflow-hidden" role="region" aria-label="Medication orders">
      <div className="panel-header flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between bg-[rgba(15,15,17,0.5)]">
        <div>
          <div className="section-label mb-1.5 flex items-center gap-1.5 text-[var(--accent)]">
            <Pill size={13} aria-hidden="true" /> Pharmacotherapy Prescriptions
          </div>
          <h2 className="text-sm font-bold text-[var(--text-primary)] uppercase">Active Medications</h2>
          <p className="mt-1 text-xs text-[var(--text-secondary)] uppercase">
            {safetyNote}
          </p>
        </div>
        <button
          type="button"
          onClick={() => void loadPrescriptions(true)}
          disabled={refreshing}
          className="btn btn-secondary text-xs flex items-center justify-center gap-1 cursor-pointer"
          aria-label="Refresh medication orders"
        >
          <RefreshCcw size={13} className={refreshing ? "animate-spin" : ""} aria-hidden="true" />
          Sync Rx
        </button>
      </div>

      <div className="p-4 space-y-3">
        <div className="flex justify-between items-center text-[10px] font-mono uppercase text-[var(--text-dim)] pb-2 border-b border-[var(--border)]">
          <span>{orderedPrescriptions.length} active orders</span>
          <span>Pharmacy log</span>
        </div>

        {loading ? (
          <div className="p-3 text-xs font-mono text-[var(--text-dim)] uppercase tracking-wider">
            Loading Rx list...
          </div>
        ) : error ? (
          <div className="flex items-center gap-1.5 p-3 text-xs font-mono text-[var(--danger)]" role="alert">
            <AlertTriangle size={13} aria-hidden="true" /> {error}
          </div>
        ) : orderedPrescriptions.length === 0 ? (
          <div className="p-3 text-xs font-mono text-[var(--text-dim)] uppercase tracking-wide">
            No medication orders logged.
          </div>
        ) : (
          <div className="space-y-3" aria-label="Medication order list">
            {orderedPrescriptions.map((prescription) => (
              <div key={prescription.id} className="space-y-2 p-2.5 rounded border border-[var(--border)] bg-[rgba(255,255,255,0.01)]">
                <div className="flex flex-wrap items-center justify-between gap-2 border-b border-[var(--border)] pb-2">
                  <span className={`px-1.5 py-0.5 rounded-sm border text-[9px] uppercase font-bold font-mono tracking-wider ${statusStyle(prescription.status)}`}>
                    {formatStatus(prescription.status)}
                  </span>
                  {prescription.diagnosis_context && (
                    <span className="mono-meta text-[9px]">{prescription.diagnosis_context}</span>
                  )}
                </div>
                
                <div className="space-y-2">
                  {prescription.items.map((item) => (
                    <div key={item.id} className="rounded border border-[var(--border-subtle)] bg-[rgba(255,255,255,0.015)] p-2">
                      <h3 className="text-xs font-bold text-[var(--text-primary)] uppercase">{item.medication_name}</h3>
                      <p className="text-[10px] font-mono text-[var(--text-secondary)] uppercase mt-0.5">
                        {item.dosage} / {item.frequency} / {item.duration}
                      </p>
                      <div className="mt-1 flex flex-wrap gap-2 text-[9px] font-mono text-[var(--text-dim)] uppercase">
                        <span>{itemQuantityText(item)}</span>
                        <span>{item.quantity_dispensed} dispensed</span>
                        <span>{formatStatus(item.status)}</span>
                      </div>
                      {item.instructions && (
                        <p className="mt-1 text-[10px] font-mono text-[var(--text-secondary)] uppercase border-t border-[var(--border-subtle)] pt-1">Notes: {item.instructions}</p>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </section>
  );
}
