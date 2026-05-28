"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";
import { BedDouble, CheckCircle2, ClipboardList, Loader2, ShieldAlert, Stethoscope } from "lucide-react";
import { useAuthStore } from "@/lib/auth";
import {
  createAdmission,
  createClinicalOrder,
  createEncounter,
  getDepartments,
  type Department,
} from "@/lib/api";
import { notifyPatientCareEventsUpdated } from "@/lib/patientCareEvents";

const staffRoles = new Set(["doctor", "admin"]);
const encounterTypes = ["OPD", "IPD", "Emergency"];
const priorities = ["routine", "urgent", "stat"];
const orderTypes = ["lab", "radiology", "pharmacy", "nursing", "procedure"];

export default function PatientCareActions({ patientId }: { patientId: number }) {
  const { user } = useAuthStore();
  const [departments, setDepartments] = useState<Department[]>([]);
  const [departmentId, setDepartmentId] = useState(0);
  const [encounterType, setEncounterType] = useState("OPD");
  const [priority, setPriority] = useState("routine");
  const [encounterReason, setEncounterReason] = useState("");
  const [admissionReason, setAdmissionReason] = useState("");
  const [orderType, setOrderType] = useState("lab");
  const [orderTitle, setOrderTitle] = useState("");
  const [activeEncounterId, setActiveEncounterId] = useState<number | null>(null);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [loadingDepartments, setLoadingDepartments] = useState(true);
  const [submitting, setSubmitting] = useState<string | null>(null);

  const canManageCare = staffRoles.has(user?.role || "");

  useEffect(() => {
    if (!canManageCare) return;
    getDepartments()
      .then((items) => {
        setDepartments(items);
        if (items.length > 0) setDepartmentId(items[0].id);
      })
      .catch((err) => setError(err.message || "Failed to load departments"))
      .finally(() => setLoadingDepartments(false));
  }, [canManageCare]);

  const departmentOptions = useMemo(() => departments.map((department) => ({
    id: department.id,
    label: `${department.name} (${department.department_type})`,
  })), [departments]);

  if (!canManageCare) {
    return (
      <section className="panel p-5" aria-label="Medical staff actions unavailable">
        <div className="mb-3 flex items-center gap-2 text-[var(--accent)]">
          <ShieldAlert size={16} aria-hidden="true" />
          <h2 className="section-title">Medical staff actions unavailable</h2>
        </div>
        <p className="text-sm leading-6 text-[var(--text-secondary)]">
          Patients can review their own record views, while encounter, admission, and order actions remain limited to authorized staff.
        </p>
      </section>
    );
  }

  async function submitEncounter(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSubmitting("encounter");
    setMessage("");
    setError("");
    try {
      const encounter = await createEncounter({
        patient_id: patientId,
        department_id: departmentId || undefined,
        encounter_type: encounterType,
        reason: encounterReason.trim() || undefined,
        priority,
      });
      setActiveEncounterId(encounter.id);
      setEncounterReason("");
      setMessage("Encounter opened");
      notifyPatientCareEventsUpdated(patientId);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to open encounter");
    } finally {
      setSubmitting(null);
    }
  }

  async function submitAdmission(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!activeEncounterId) return;
    setSubmitting("admission");
    setMessage("");
    setError("");
    try {
      await createAdmission({
        encounter_id: activeEncounterId,
        patient_id: patientId,
        department_id: departmentId || undefined,
        reason: admissionReason.trim() || undefined,
      });
      setAdmissionReason("");
      setMessage("Admission created");
      notifyPatientCareEventsUpdated(patientId);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create admission");
    } finally {
      setSubmitting(null);
    }
  }

  async function submitOrder(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSubmitting("order");
    setMessage("");
    setError("");
    try {
      await createClinicalOrder({
        encounter_id: activeEncounterId || undefined,
        patient_id: patientId,
        department_id: departmentId || undefined,
        order_type: orderType,
        title: orderTitle.trim(),
        priority,
      });
      setOrderTitle("");
      setMessage("Order created");
      notifyPatientCareEventsUpdated(patientId);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create order");
    } finally {
      setSubmitting(null);
    }
  }

  return (
    <section className="panel overflow-hidden" aria-labelledby="care-actions-title">
      <div className="panel-header flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
        <div>
          <div className="section-label mb-2 flex items-center gap-2 text-[var(--accent)]">
            <Stethoscope size={13} aria-hidden="true" />
            Staff workflow
          </div>
          <h2 id="care-actions-title" className="text-xl font-semibold text-[var(--text-primary)]">
            Care Workflow Actions
          </h2>
          <p className="mt-2 max-w-3xl text-sm leading-6 text-[var(--text-secondary)]">
            Open clinician-reviewed encounters, create admissions, and place department orders from this patient record.
          </p>
        </div>
        <div className="status-badge status-badge-accent">
          {activeEncounterId ? `Encounter #${activeEncounterId} active` : loadingDepartments ? "Loading departments" : "No active encounter"}
        </div>
      </div>

      <div className="grid grid-cols-1 gap-5 p-5 xl:grid-cols-3">
        <form className="rounded-lg border border-[var(--border)] bg-[var(--bg-card)] p-4" onSubmit={submitEncounter}>
          <h3 className="section-title mb-4 flex items-center gap-2">
            <Stethoscope size={14} aria-hidden="true" />
            Open Encounter
          </h3>
          <div className="space-y-3">
            <select
              aria-label="Encounter department"
              className="input-clinical"
              value={departmentId || ""}
              onChange={(event) => setDepartmentId(Number(event.target.value))}
            >
              {departmentOptions.map((department) => (
                <option key={department.id} value={department.id}>{department.label}</option>
              ))}
            </select>
            <select
              aria-label="Encounter type"
              className="input-clinical"
              value={encounterType}
              onChange={(event) => setEncounterType(event.target.value)}
            >
              {encounterTypes.map((type) => (
                <option key={type} value={type}>{type}</option>
              ))}
            </select>
            <select
              aria-label="Encounter priority"
              className="input-clinical"
              value={priority}
              onChange={(event) => setPriority(event.target.value)}
            >
              {priorities.map((item) => (
                <option key={item} value={item}>{item}</option>
              ))}
            </select>
            <input
              aria-label="Encounter reason"
              className="input-clinical"
              placeholder="Reason for encounter"
              value={encounterReason}
              onChange={(event) => setEncounterReason(event.target.value)}
            />
            <button className="btn btn-primary w-full" type="submit" disabled={submitting === "encounter" || departments.length === 0}>
              {submitting === "encounter" ? <Loader2 size={14} className="animate-spin" aria-hidden="true" /> : <Stethoscope size={14} aria-hidden="true" />}
              Open encounter
            </button>
          </div>
        </form>

        <form className="rounded-lg border border-[var(--border)] bg-[var(--bg-card)] p-4" onSubmit={submitAdmission}>
          <h3 className="section-title mb-4 flex items-center gap-2">
            <BedDouble size={14} aria-hidden="true" />
            Admission
          </h3>
          <div className="space-y-3">
            <div className="rounded-md border border-[var(--border)] bg-[rgba(255,244,230,0.025)] px-3 py-2 text-sm text-[var(--text-secondary)]">
              {activeEncounterId ? `Linked to encounter #${activeEncounterId}` : "Open an encounter before admission"}
            </div>
            <input
              aria-label="Admission reason"
              className="input-clinical"
              placeholder="Admission reason"
              value={admissionReason}
              onChange={(event) => setAdmissionReason(event.target.value)}
            />
            <button className="btn btn-secondary w-full" type="submit" disabled={!activeEncounterId || submitting === "admission"}>
              {submitting === "admission" ? <Loader2 size={14} className="animate-spin" aria-hidden="true" /> : <BedDouble size={14} aria-hidden="true" />}
              Create admission
            </button>
          </div>
        </form>

        <form className="rounded-lg border border-[var(--border)] bg-[var(--bg-card)] p-4" onSubmit={submitOrder}>
          <h3 className="section-title mb-4 flex items-center gap-2">
            <ClipboardList size={14} aria-hidden="true" />
            Clinical Order
          </h3>
          <div className="space-y-3">
            <select
              aria-label="Order type"
              className="input-clinical"
              value={orderType}
              onChange={(event) => setOrderType(event.target.value)}
            >
              {orderTypes.map((type) => (
                <option key={type} value={type}>{type}</option>
              ))}
            </select>
            <input
              aria-label="Order title"
              className="input-clinical"
              placeholder="Order title"
              required
              value={orderTitle}
              onChange={(event) => setOrderTitle(event.target.value)}
            />
            <button className="btn btn-secondary w-full" type="submit" disabled={submitting === "order" || departments.length === 0}>
              {submitting === "order" ? <Loader2 size={14} className="animate-spin" aria-hidden="true" /> : <ClipboardList size={14} aria-hidden="true" />}
              Create order
            </button>
          </div>
        </form>
      </div>

      {(message || error) && (
        <div className="border-t border-[var(--border)] bg-[var(--bg-primary)] px-5 py-3">
          {message && (
            <div className="flex items-center gap-2 text-sm text-[var(--success)]" role="status">
              <CheckCircle2 size={14} aria-hidden="true" />
              {message}
            </div>
          )}
          {error && (
            <div className="flex items-center gap-2 text-sm text-[var(--danger)]" role="alert">
              <ShieldAlert size={14} aria-hidden="true" />
              {error}
            </div>
          )}
        </div>
      )}
    </section>
  );
}
