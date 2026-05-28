"use client";

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

const DEFAULT_CLINICAL_NOTE = "Prescriptions support clinician and pharmacist workflows; clinicians remain responsible for treatment decisions.";
const PATIENT_MEDICATION_NOTE = "Medication details are for review. Patients should consult a qualified clinician or pharmacist before changing medicines, and emergencies require immediate hospital or local emergency care.";

function statusStyle(status: string) {
  const normalized = status.toLowerCase();
  if (normalized === "dispensed") {
    return "border-[var(--success-border)] bg-[var(--success-muted)] text-[var(--success)]";
  }
  if (normalized === "partially_dispensed") {
    return "border-[var(--warning)]/30 bg-[var(--warning-muted)] text-[var(--warning)]";
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
  return `${item.quantity_prescribed} prescribed`;
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

  const canViewDoctorPrescriptions = user?.role === "doctor";
  const canViewPatientPrescriptions = user?.role === "patient" && user.id === patientId;
  const canLoadPrescriptions = canViewDoctorPrescriptions || canViewPatientPrescriptions;

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
      if (canViewDoctorPrescriptions) {
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
  }, [canLoadPrescriptions, canViewDoctorPrescriptions, patientId]);

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
      <div className="panel p-5" role="region" aria-label="Active medications">
        <h3 className="section-label mb-4">Medications</h3>
        <div className="rounded-md border border-[var(--border)] bg-[var(--bg-card)] p-4 text-sm leading-6 text-[var(--text-secondary)]">
          No active medication data loaded from source systems for this patient record.
        </div>
      </div>
    );
  }

  return (
    <section className="panel p-5" role="region" aria-label="Medication orders">
      <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between xl:flex-col">
        <div>
          <div className="section-label mb-2 flex items-center gap-2">
            <Pill size={14} aria-hidden="true" /> Pharmacy
          </div>
          <h2 className="text-lg font-semibold text-[var(--text-primary)]">Medication Orders</h2>
          <p className="mt-1 text-sm text-[var(--text-secondary)]">
            {safetyNote}
          </p>
        </div>
        <button
          type="button"
          onClick={() => void loadPrescriptions(true)}
          disabled={refreshing}
          className="btn btn-secondary flex items-center justify-center gap-2 text-xs font-semibold uppercase tracking-wider"
          aria-label="Refresh medication orders"
        >
          <RefreshCcw size={14} className={refreshing ? "animate-spin" : ""} aria-hidden="true" />
          {refreshing ? "Refreshing" : "Refresh"}
        </button>
      </div>

      <div className="mt-4 rounded border border-[var(--border)] bg-[var(--bg-primary)]">
        <div className="border-b border-[var(--border)] px-4 py-2">
          <span className="mono-meta">{orderedPrescriptions.length} prescriptions</span>
        </div>

        {loading ? (
          <div className="p-4 text-sm text-[var(--text-secondary)]" role="status">
            Loading medication orders
          </div>
        ) : error ? (
          <div className="flex items-center gap-2 p-4 text-sm text-[var(--danger)]" role="alert">
            <AlertTriangle size={16} aria-hidden="true" /> {error}
          </div>
        ) : orderedPrescriptions.length === 0 ? (
          <div className="p-4 text-sm text-[var(--text-secondary)]">
            No medication orders recorded for this patient.
          </div>
        ) : (
          <ul className="divide-y divide-[var(--border)]" aria-label="Medication order list">
            {orderedPrescriptions.map((prescription) => (
              <li key={prescription.id} className="p-4">
                <div className="mb-3 flex flex-wrap items-center gap-2">
                  <span className={`rounded border px-2 py-1 text-[10px] uppercase tracking-widest ${statusStyle(prescription.status)}`}>
                    {formatStatus(prescription.status)}
                  </span>
                  {prescription.diagnosis_context && (
                    <span className="mono-meta">{prescription.diagnosis_context}</span>
                  )}
                </div>
                <ul className="space-y-3" aria-label={`Prescription ${prescription.id} items`}>
                  {prescription.items.map((item) => (
                    <li key={item.id} className="rounded border border-[var(--border)] bg-[var(--bg-secondary)] p-3">
                      <h3 className="text-sm font-semibold text-[var(--text-primary)]">{item.medication_name}</h3>
                      <p className="mt-1 text-sm text-[var(--text-secondary)]">
                        {item.dosage} / {item.frequency} / {item.duration}
                      </p>
                      <div className="mt-2 flex flex-wrap gap-2">
                        <span className="mono-meta">{itemQuantityText(item)}</span>
                        <span className="mono-meta">{item.quantity_dispensed} dispensed</span>
                        <span className="mono-meta">{formatStatus(item.status)}</span>
                      </div>
                      {item.instructions && (
                        <p className="mt-2 text-xs text-[var(--text-secondary)]">{item.instructions}</p>
                      )}
                    </li>
                  ))}
                </ul>
              </li>
            ))}
          </ul>
        )}
      </div>
    </section>
  );
}
