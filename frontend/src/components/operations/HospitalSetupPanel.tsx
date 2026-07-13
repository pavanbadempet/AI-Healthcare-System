
import { FormEvent, useEffect, useMemo, useState } from "react";
import { BedDouble, Building2, CheckCircle2, Loader2, Plus, ShieldAlert, Layers } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
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
      setMessage("Department created successfully.");
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
      setMessage("Bed registered successfully.");
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
          <div className="section-label mb-1.5 flex items-center gap-2 text-[var(--accent)] tracking-wider">
            <Building2 size={12} className="text-[var(--accent)]" aria-hidden="true" />
            Infrastructure System
          </div>
          <h2 id="hospital-setup-title" className="text-lg font-bold text-[var(--text-primary)] uppercase tracking-wide">
            Onboarding & Facility Map
          </h2>
          <p className="mt-1 max-w-3xl text-xs text-[var(--text-secondary)] font-mono uppercase">
            Configure clinic divisions and bed inventory context.
          </p>
        </div>
        <div className="status-badge status-badge-accent font-mono text-[9px] px-2.5 py-0.5 self-start md:self-auto">
          {loading ? (
            <span className="flex items-center gap-1">
              <Loader2 size={10} className="animate-spin" aria-hidden="true" /> Syncing...
            </span>
          ) : (
            `${departments.length} ACTIVE DIVISIONS`
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 gap-5 p-5 xl:grid-cols-[1.1fr_1.1fr_0.8fr]">
        
        {/* Create Department Form */}
        <motion.div 
          initial={{ opacity: 0, y: 5 }} 
          animate={{ opacity: 1, y: 0 }} 
          transition={{ duration: 0.2 }}
          className="rounded border border-[var(--border)] bg-[rgba(24,24,27,0.2)] p-5 flex flex-col justify-between hover:border-[var(--border-focus)] transition-colors"
        >
          <div>
            <h3 className="section-title mb-4 flex items-center gap-2 font-bold text-xs uppercase tracking-wider text-[var(--text-primary)]">
              <Plus size={13} className="text-[var(--accent)]" aria-hidden="true" />
              Register Department
            </h3>
            <form onSubmit={submitDepartment} className="space-y-4">
              <div className="space-y-1">
                <label className="section-label text-[9px]" htmlFor="dept-name">Department Name</label>
                <input
                  id="dept-name"
                  aria-label="Department name"
                  className="input-clinical font-mono uppercase"
                  placeholder="e.g. Intensive Care Unit"
                  required
                  value={departmentForm.name}
                  onChange={(event) => setDepartmentForm((current) => ({ ...current, name: event.target.value }))}
                />
              </div>

              <div className="space-y-1">
                <label className="section-label text-[9px]" htmlFor="dept-type">Department Type</label>
                <select
                  id="dept-type"
                  aria-label="Department type"
                  className="input-clinical font-mono uppercase bg-[var(--bg-card)]"
                  value={departmentForm.department_type}
                  onChange={(event) => setDepartmentForm((current) => ({ ...current, department_type: event.target.value }))}
                >
                  {departmentTypes.map((type) => (
                    <option key={type} value={type} className="bg-[var(--bg-card)]">{type}</option>
                  ))}
                </select>
              </div>

              <div className="space-y-1">
                <label className="section-label text-[9px]" htmlFor="dept-location">Location / Block</label>
                <input
                  id="dept-location"
                  aria-label="Department location"
                  className="input-clinical font-mono uppercase"
                  placeholder="e.g. Wing B, 3rd Floor"
                  value={departmentForm.location || ""}
                  onChange={(event) => setDepartmentForm((current) => ({ ...current, location: event.target.value }))}
                />
              </div>

              <button className="btn btn-primary w-full mt-2 uppercase font-mono tracking-wider cursor-pointer" type="submit" disabled={savingDepartment}>
                {savingDepartment ? (
                  <Loader2 size={13} className="animate-spin" aria-hidden="true" />
                ) : (
                  <>
                    <Plus size={13} aria-hidden="true" />
                    Register Division
                  </>
                )}
              </button>
            </form>
          </div>
        </motion.div>

        {/* Create Bed Form */}
        <motion.div 
          initial={{ opacity: 0, y: 5 }} 
          animate={{ opacity: 1, y: 0 }} 
          transition={{ duration: 0.2, delay: 0.05 }}
          className="rounded border border-[var(--border)] bg-[rgba(24,24,27,0.2)] p-5 flex flex-col justify-between hover:border-[var(--border-focus)] transition-colors"
        >
          <div>
            <h3 className="section-title mb-4 flex items-center gap-2 font-bold text-xs uppercase tracking-wider text-[var(--text-primary)]">
              <BedDouble size={13} className="text-[var(--accent-purple)]" aria-hidden="true" />
              Register Bed Node
            </h3>
            <form onSubmit={submitBed} className="space-y-4">
              <div className="space-y-1">
                <label className="section-label text-[9px]" htmlFor="bed-dept">Target Division</label>
                <select
                  id="bed-dept"
                  aria-label="Bed department"
                  className="input-clinical font-mono uppercase bg-[var(--bg-card)]"
                  required
                  value={bedForm.department_id || ""}
                  onChange={(event) => setBedForm((current) => ({ ...current, department_id: Number(event.target.value) }))}
                  disabled={departments.length === 0}
                >
                  {departments.length === 0 ? (
                    <option value="" className="bg-[var(--bg-card)]">-- CREATE A DEPT FIRST --</option>
                  ) : (
                    departmentOptions.map((department) => (
                      <option key={department.id} value={department.id} className="bg-[var(--bg-card)]">
                        {department.label}
                      </option>
                    ))
                  )}
                </select>
              </div>

              <div className="space-y-1">
                <label className="section-label text-[9px]" htmlFor="bed-num">Bed Number / Identifier</label>
                <input
                  id="bed-num"
                  aria-label="Bed number"
                  className="input-clinical font-mono uppercase"
                  placeholder="e.g. Bed-402-A"
                  required
                  value={bedForm.bed_number}
                  onChange={(event) => setBedForm((current) => ({ ...current, bed_number: event.target.value }))}
                />
              </div>

              <div className="space-y-1">
                <label className="section-label text-[9px]" htmlFor="bed-ward">Ward / Area</label>
                <input
                  id="bed-ward"
                  aria-label="Ward"
                  className="input-clinical font-mono uppercase"
                  placeholder="e.g. General Med-Surg"
                  value={bedForm.ward || ""}
                  onChange={(event) => setBedForm((current) => ({ ...current, ward: event.target.value }))}
                />
              </div>

              <button 
                className="btn btn-secondary w-full mt-2 uppercase font-mono tracking-wider cursor-pointer" 
                type="submit" 
                disabled={savingBed || departments.length === 0}
              >
                {savingBed ? (
                  <Loader2 size={13} className="animate-spin" aria-hidden="true" />
                ) : (
                  <>
                    <BedDouble size={13} aria-hidden="true" />
                    Register Bed Node
                  </>
                )}
              </button>
            </form>
          </div>
        </motion.div>

        {/* Configured Departments List */}
        <motion.div 
          initial={{ opacity: 0, y: 5 }} 
          animate={{ opacity: 1, y: 0 }} 
          transition={{ duration: 0.2, delay: 0.1 }}
          className="rounded border border-[var(--border)] bg-[rgba(24,24,27,0.2)] p-5 flex flex-col justify-between hover:border-[var(--border-focus)] transition-colors"
        >
          <div className="flex flex-col h-full">
            <h3 className="section-title mb-4 flex items-center gap-2 font-bold text-xs uppercase tracking-wider text-[var(--text-primary)]">
              <Layers size={13} className="text-[var(--accent-blue)]" aria-hidden="true" />
              Active Divisions
            </h3>
            
            <AnimatePresence mode="popLayout">
              {message && (
                <motion.div 
                  initial={{ opacity: 0, height: 0, marginBottom: 0 }}
                  animate={{ opacity: 1, height: "auto", marginBottom: 12 }}
                  exit={{ opacity: 0, height: 0, marginBottom: 0 }}
                  className="flex items-center gap-2 rounded border border-[var(--success-border)] bg-[var(--success-muted)] px-3 py-2 text-[10px] font-mono uppercase text-[var(--success)]" 
                  role="status"
                >
                  <CheckCircle2 size={12} className="shrink-0" aria-hidden="true" />
                  <span>{message}</span>
                </motion.div>
              )}
              {error && (
                <motion.div 
                  initial={{ opacity: 0, height: 0, marginBottom: 0 }}
                  animate={{ opacity: 1, height: "auto", marginBottom: 12 }}
                  exit={{ opacity: 0, height: 0, marginBottom: 0 }}
                  className="flex items-center gap-2 rounded border border-[var(--danger-border)] bg-[var(--danger-muted)] px-3 py-2 text-[10px] font-mono uppercase text-[var(--danger)]" 
                  role="alert"
                >
                  <ShieldAlert size={12} className="shrink-0" aria-hidden="true" />
                  <span>{error}</span>
                </motion.div>
              )}
            </AnimatePresence>

            <div className="flex-1 max-h-[220px] overflow-y-auto space-y-2 pr-1 custom-scrollbar">
              {departments.length > 0 ? (
                departments.map((department) => (
                  <div 
                    key={department.id} 
                    className="rounded border border-[var(--border)] bg-[rgba(255,255,255,0.01)] hover:bg-[rgba(255,255,255,0.02)] p-3 transition-colors"
                  >
                    <div className="flex justify-between items-start gap-2">
                      <p className="text-xs font-bold text-[var(--text-primary)] uppercase tracking-wide truncate">{department.name}</p>
                      <span className="text-[9px] font-mono font-extrabold text-[var(--accent)] border border-[var(--accent-border)] bg-[var(--accent-muted)] px-1.5 py-0.5 rounded shrink-0">
                        {department.department_type}
                      </span>
                    </div>
                    {department.location && (
                      <p className="mono-meta mt-1.5 text-[9px] text-[var(--text-secondary)] font-mono uppercase">
                        LOC: {department.location}
                      </p>
                    )}
                  </div>
                ))
              ) : (
                <div className="h-full flex flex-col items-center justify-center text-center p-6 border border-dashed border-[var(--border)] rounded">
                  <p className="text-[10px] font-mono text-[var(--text-dim)] uppercase">No departments configured yet.</p>
                </div>
              )}
            </div>
          </div>
        </motion.div>

      </div>
    </section>
  );
}
