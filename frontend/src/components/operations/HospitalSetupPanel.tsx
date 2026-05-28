"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";
import { BedDouble, Building2, CheckCircle2, Loader2, Plus, ShieldAlert } from "lucide-react";
import {
  createBed,
  createDepartment,
  getDepartments,
  type BedCreate,
  type Department,
  type DepartmentCreate,
} from "@/lib/api";

const departmentTypes = ["OPD", "IPD", "Emergency", "Diagnostics", "Pharmacy", "Nursing", "Administration"];

export default function HospitalSetupPanel() {
  const [departments, setDepartments] = useState<Department[]>([]);
  const [departmentForm, setDepartmentForm] = useState<DepartmentCreate>({
    name: "",
    department_type: "OPD",
    location: "",
  });
  const [bedForm, setBedForm] = useState<BedCreate>({
    department_id: 0,
    bed_number: "",
    ward: "",
    status: "available",
  });
  const [loading, setLoading] = useState(true);
  const [savingDepartment, setSavingDepartment] = useState(false);
  const [savingBed, setSavingBed] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    getDepartments()
      .then((items) => {
        setDepartments(items);
        if (items.length > 0) {
          setBedForm((current) => ({ ...current, department_id: current.department_id || items[0].id }));
        }
      })
      .catch((err) => setError(err.message || "Failed to load departments"))
      .finally(() => setLoading(false));
  }, []);

  const departmentOptions = useMemo(() => departments.map((department) => ({
    id: department.id,
    label: `${department.name} (${department.department_type})`,
  })), [departments]);

  async function submitDepartment(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSavingDepartment(true);
    setMessage("");
    setError("");
    try {
      const created = await createDepartment({
        name: departmentForm.name.trim(),
        department_type: departmentForm.department_type,
        location: departmentForm.location?.trim() || undefined,
      });
      setDepartments((current) => [...current, created]);
      setBedForm((current) => ({ ...current, department_id: current.department_id || created.id }));
      setDepartmentForm({ name: "", department_type: "OPD", location: "" });
      setMessage("Department created");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create department");
    } finally {
      setSavingDepartment(false);
    }
  }

  async function submitBed(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSavingBed(true);
    setMessage("");
    setError("");
    try {
      await createBed({
        department_id: Number(bedForm.department_id),
        bed_number: bedForm.bed_number.trim(),
        ward: bedForm.ward?.trim() || undefined,
        status: bedForm.status || "available",
      });
      setBedForm((current) => ({ ...current, bed_number: "", ward: "", status: "available" }));
      setMessage("Bed created");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create bed");
    } finally {
      setSavingBed(false);
    }
  }

  return (
    <section className="panel overflow-hidden" aria-labelledby="hospital-setup-title">
      <div className="panel-header flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
        <div>
          <div className="section-label mb-2 flex items-center gap-2 text-[var(--accent)]">
            <Building2 size={13} aria-hidden="true" />
            Hospital onboarding
          </div>
          <h2 id="hospital-setup-title" className="text-xl font-semibold text-[var(--text-primary)]">
            Department and Bed Setup
          </h2>
          <p className="mt-2 max-w-3xl text-sm leading-6 text-[var(--text-secondary)]">
            Configure the facility structure used by OPD, IPD, emergency, admission, and bed-capacity workflows.
          </p>
        </div>
        <div className="status-badge status-badge-accent">
          {loading ? "Loading setup" : `${departments.length} departments`}
        </div>
      </div>

      <div className="grid grid-cols-1 gap-5 p-5 xl:grid-cols-[1fr_1fr_0.9fr]">
        <form className="rounded-lg border border-[var(--border)] bg-[var(--bg-card)] p-4" onSubmit={submitDepartment}>
          <h3 className="section-title mb-4 flex items-center gap-2">
            <Plus size={14} aria-hidden="true" />
            Create Department
          </h3>
          <div className="space-y-3">
            <input
              aria-label="Department name"
              className="input-clinical"
              placeholder="Department name"
              required
              value={departmentForm.name}
              onChange={(event) => setDepartmentForm((current) => ({ ...current, name: event.target.value }))}
            />
            <select
              aria-label="Department type"
              className="input-clinical"
              value={departmentForm.department_type}
              onChange={(event) => setDepartmentForm((current) => ({ ...current, department_type: event.target.value }))}
            >
              {departmentTypes.map((type) => (
                <option key={type} value={type}>{type}</option>
              ))}
            </select>
            <input
              aria-label="Department location"
              className="input-clinical"
              placeholder="Location"
              value={departmentForm.location || ""}
              onChange={(event) => setDepartmentForm((current) => ({ ...current, location: event.target.value }))}
            />
            <button className="btn btn-primary w-full" type="submit" disabled={savingDepartment}>
              {savingDepartment ? <Loader2 size={14} className="animate-spin" aria-hidden="true" /> : <Plus size={14} aria-hidden="true" />}
              Create department
            </button>
          </div>
        </form>

        <form className="rounded-lg border border-[var(--border)] bg-[var(--bg-card)] p-4" onSubmit={submitBed}>
          <h3 className="section-title mb-4 flex items-center gap-2">
            <BedDouble size={14} aria-hidden="true" />
            Create Bed
          </h3>
          <div className="space-y-3">
            <select
              aria-label="Bed department"
              className="input-clinical"
              required
              value={bedForm.department_id || ""}
              onChange={(event) => setBedForm((current) => ({ ...current, department_id: Number(event.target.value) }))}
            >
              {departmentOptions.map((department) => (
                <option key={department.id} value={department.id}>{department.label}</option>
              ))}
            </select>
            <input
              aria-label="Bed number"
              className="input-clinical"
              placeholder="Bed number"
              required
              value={bedForm.bed_number}
              onChange={(event) => setBedForm((current) => ({ ...current, bed_number: event.target.value }))}
            />
            <input
              aria-label="Ward"
              className="input-clinical"
              placeholder="Ward"
              value={bedForm.ward || ""}
              onChange={(event) => setBedForm((current) => ({ ...current, ward: event.target.value }))}
            />
            <button className="btn btn-secondary w-full" type="submit" disabled={savingBed || departments.length === 0}>
              {savingBed ? <Loader2 size={14} className="animate-spin" aria-hidden="true" /> : <BedDouble size={14} aria-hidden="true" />}
              Create bed
            </button>
          </div>
        </form>

        <div className="rounded-lg border border-[var(--border)] bg-[var(--bg-card)] p-4">
          <h3 className="section-title mb-4">Configured Departments</h3>
          {message && (
            <div className="mb-3 flex items-center gap-2 rounded-md border border-[var(--success-border)] bg-[var(--success-muted)] px-3 py-2 text-sm text-[var(--success)]" role="status">
              <CheckCircle2 size={14} aria-hidden="true" />
              {message}
            </div>
          )}
          {error && (
            <div className="mb-3 flex items-center gap-2 rounded-md border border-[var(--danger-border)] bg-[var(--danger-muted)] px-3 py-2 text-sm text-[var(--danger)]" role="alert">
              <ShieldAlert size={14} aria-hidden="true" />
              {error}
            </div>
          )}
          <div className="max-h-64 space-y-2 overflow-y-auto">
            {departments.length > 0 ? departments.map((department) => (
              <div key={department.id} className="rounded-md border border-[var(--border)] bg-[rgba(255,244,230,0.025)] p-3">
                <p className="text-sm font-semibold text-[var(--text-primary)]">{department.name}</p>
                <p className="mono-meta mt-1">{department.department_type} {department.location ? `- ${department.location}` : ""}</p>
              </div>
            )) : (
              <p className="text-sm text-[var(--text-dim)]">No departments configured yet.</p>
            )}
          </div>
        </div>
      </div>
    </section>
  );
}
