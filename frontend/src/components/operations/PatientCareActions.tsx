
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
      <section className="panel p-4" aria-label="Medical staff actions unavailable">
        <div className="mb-2 flex items-center gap-1.5 text-[var(--accent)]">
          <ShieldAlert size={14} aria-hidden="true" />
          <h2 className="section-title">Encounter control inactive</h2>
        </div>
        <p className="text-xs leading-relaxed text-[var(--text-secondary)] uppercase font-mono">
          Clinical action triggers remain scoped to authorized medical staff profiles.
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
      setMessage("Encounter opened successfully");
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
      setMessage("Admission created successfully");
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
      setMessage("Order created successfully");
      notifyPatientCareEventsUpdated(patientId);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create order");
    } finally {
      setSubmitting(null);
    }
  }

  return (
    <section className="panel overflow-hidden" aria-labelledby="care-actions-title">
      <div className="panel-header flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between bg-[rgba(15,15,17,0.5)]">
        <div>
          <div className="section-label mb-1.5 flex items-center gap-1.5 text-[var(--accent)]">
            <Stethoscope size={13} aria-hidden="true" />
            Clinical Interventions
          </div>
          <h2 id="care-actions-title" className="text-sm font-bold text-[var(--text-primary)] uppercase">Care Workflow Controls</h2>
          <p className="mt-1 text-xs text-[var(--text-secondary)] uppercase">
            Onboard patients, declare admissions, and route diagnostic clinical orders.
          </p>
        </div>
        <div className="status-badge status-badge-accent">
          {activeEncounterId ? `Active Encounter: #${activeEncounterId}` : loadingDepartments ? "Loading nodes..." : "Awaiting encounter"}
        </div>
      </div>

      <div className="grid grid-cols-1 gap-4 p-4 xl:grid-cols-3">
        <form className="rounded border border-[var(--border)] bg-[rgba(255,255,255,0.01)] p-4 space-y-4" onSubmit={submitEncounter}>
          <h3 className="section-title flex items-center gap-2 border-b border-[var(--border)] pb-2">
            <Stethoscope size={13} aria-hidden="true" />
            Encounter Node
          </h3>
          <div className="space-y-3">
            <div>
              <label className="section-label mb-1 block">Department</label>
              <select
                aria-label="Encounter department"
                className="input-clinical"
                value={departmentId || ""}
                onChange={(event) => setDepartmentId(Number(event.target.value))}
              >
                {departmentOptions.map((department) => (
                  <option key={department.id} value={department.id} className="bg-[var(--bg-card)]">{department.label}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="section-label mb-1 block">Encounter Mode</label>
              <select
                aria-label="Encounter type"
                className="input-clinical"
                value={encounterType}
                onChange={(event) => setEncounterType(event.target.value)}
              >
                {encounterTypes.map((type) => (
                  <option key={type} value={type} className="bg-[var(--bg-card)]">{type}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="section-label mb-1 block">Priority Level</label>
              <select
                aria-label="Encounter priority"
                className="input-clinical"
                value={priority}
                onChange={(event) => setPriority(event.target.value)}
              >
                {priorities.map((item) => (
                  <option key={item} value={item} className="bg-[var(--bg-card)]">{item.toUpperCase()}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="section-label mb-1 block">Diagnosis/Reason</label>
              <input
                aria-label="Encounter reason"
                className="input-clinical"
                placeholder="Reason for consult"
                value={encounterReason}
                onChange={(event) => setEncounterReason(event.target.value)}
              />
            </div>
            <button className="btn btn-primary w-full cursor-pointer py-2" type="submit" disabled={submitting === "encounter" || departments.length === 0}>
              {submitting === "encounter" ? <Loader2 size={13} className="animate-spin" aria-hidden="true" /> : <Stethoscope size={13} aria-hidden="true" />}
              Open Encounter
            </button>
          </div>
        </form>

        <form className="rounded border border-[var(--border)] bg-[rgba(255,255,255,0.01)] p-4 space-y-4" onSubmit={submitAdmission}>
          <h3 className="section-title flex items-center gap-2 border-b border-[var(--border)] pb-2">
            <BedDouble size={13} aria-hidden="true" />
            Admission Node
          </h3>
          <div className="space-y-3">
            <div className="rounded border border-[var(--border)] bg-[#09090b] px-3.5 py-2.5 text-xs font-mono text-[var(--text-secondary)] uppercase">
              {activeEncounterId ? `Encounter #${activeEncounterId} linked` : "Open encounter to link admission"}
            </div>
            <div>
              <label className="section-label mb-1 block">Admission Reason</label>
              <input
                aria-label="Admission reason"
                className="input-clinical"
                placeholder="Admit details"
                value={admissionReason}
                onChange={(event) => setAdmissionReason(event.target.value)}
              />
            </div>
            <button className="btn btn-secondary w-full cursor-pointer py-2" type="submit" disabled={!activeEncounterId || submitting === "admission"}>
              {submitting === "admission" ? <Loader2 size={13} className="animate-spin" aria-hidden="true" /> : <BedDouble size={13} aria-hidden="true" />}
              Create Admission
            </button>
          </div>
        </form>

        <form className="rounded border border-[var(--border)] bg-[rgba(255,255,255,0.01)] p-4 space-y-4" onSubmit={submitOrder}>
          <h3 className="section-title flex items-center gap-2 border-b border-[var(--border)] pb-2">
            <ClipboardList size={13} aria-hidden="true" />
            Clinical Order
          </h3>
          <div className="space-y-3">
            <div>
              <label className="section-label mb-1 block">Order Category</label>
              <select
                aria-label="Order type"
                className="input-clinical"
                value={orderType}
                onChange={(event) => setOrderType(event.target.value)}
              >
                {orderTypes.map((type) => (
                  <option key={type} value={type} className="bg-[var(--bg-card)]">{type.toUpperCase()}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="section-label mb-1 block">Order Parameters</label>
              <input
                aria-label="Order title"
                className="input-clinical"
                placeholder="Diagnostic order parameters"
                required
                value={orderTitle}
                onChange={(event) => setOrderTitle(event.target.value)}
              />
            </div>
            <button className="btn btn-secondary w-full cursor-pointer py-2" type="submit" disabled={submitting === "order" || departments.length === 0}>
              {submitting === "order" ? <Loader2 size={13} className="animate-spin" aria-hidden="true" /> : <ClipboardList size={13} aria-hidden="true" />}
              Place Order
            </button>
          </div>
        </form>
      </div>

      {(message || error) && (
        <div className="border-t border-[var(--border)] bg-[rgba(15,15,17,0.5)] px-4 py-2 flex items-center justify-between font-mono text-xs uppercase">
          {message && (
            <div className="flex items-center gap-1.5 text-[var(--success)]" role="status">
              <CheckCircle2 size={13} aria-hidden="true" />
              {message}
            </div>
          )}
          {error && (
            <div className="flex items-center gap-1.5 text-[var(--danger)]" role="alert">
              <ShieldAlert size={13} aria-hidden="true" />
              {error}
            </div>
          )}
        </div>
      )}
    </section>
  );
}
