import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { getAdminPatients, getDoctorPatients, type DoctorPatientSummary, type UserProfile } from "@/lib/api";
import { useAuthStore } from "@/lib/auth";
import { motion } from "framer-motion";
import { Users, Search, Filter, ShieldAlert, Activity, AlertTriangle, ChevronRight, Stethoscope } from "lucide-react";

const VERIFIED_RISK_LEVELS = ["LOW", "MODERATE", "HIGH", "CRITICAL"] as const;
const RISK_FILTERS = ["ALL", "REVIEW", ...VERIFIED_RISK_LEVELS] as const;
type RegistryRiskLevel = typeof RISK_FILTERS[number] extends "ALL" ? never : Exclude<typeof RISK_FILTERS[number], "ALL">;
type RiskFilter = typeof RISK_FILTERS[number];

interface RegistryPatient {
  id: number;
  username: string;
  email?: string;
  full_name: string;
  role: "patient";
  gender?: string;
  dob?: string;
  blood_type?: string;
  latest_encounter_type?: string | null;
  latest_status?: string | null;
  open_orders?: number;
  active_admissions?: number;
  clinical_risk_level?: RegistryRiskLevel | null;
  attending_name?: string | null;
}

function adminUserToRegistryPatient(user: UserProfile): RegistryPatient {
  return {
    id: user.id,
    username: user.username,
    email: user.email,
    full_name: user.full_name || user.username,
    role: "patient",
    gender: user.gender,
    dob: user.dob,
    blood_type: user.blood_type,
  };
}

function doctorSummaryToRegistryPatient(summary: DoctorPatientSummary): RegistryPatient {
  return {
    id: summary.patient_id,
    username: summary.username,
    full_name: summary.full_name || summary.username,
    role: "patient",
    latest_encounter_type: summary.latest_encounter_type,
    latest_status: summary.latest_status,
    open_orders: summary.open_orders,
    active_admissions: summary.active_admissions,
  };
}

function calculateAge(dob: string, today = new Date()) {
  const birthDate = new Date(`${dob}T00:00:00`);
  if (Number.isNaN(birthDate.getTime())) return null;

  let age = today.getFullYear() - birthDate.getFullYear();
  const monthDelta = today.getMonth() - birthDate.getMonth();
  if (monthDelta < 0 || (monthDelta === 0 && today.getDate() < birthDate.getDate())) {
    age -= 1;
  }

  return Math.max(age, 0);
}

function registryDisplayForPatient(patient: RegistryPatient) {
  const mrn = `MRN-${(patient.id * 1024 + 100000).toString().substring(0,6)}`;
  const risk = patient.clinical_risk_level || "REVIEW";
  const diagnosis = "Primary diagnosis not recorded";
  const unit = patient.latest_encounter_type || "Not assigned";
  const attending = patient.attending_name || "Not recorded";
  const dob = patient.dob || "Not recorded";
  const age = patient.dob ? calculateAge(patient.dob) : null;
  const telemetryStatus = "No verified telemetry";

  return {
    age,
    diagnosis,
    dob,
    attending,
    isHighRisk: risk === "HIGH" || risk === "CRITICAL",
    mrn,
    risk,
    telemetryStatus,
    unit,
  };
}

function patientMatchesSearch(
  patient: RegistryPatient,
  query: string,
  display = registryDisplayForPatient(patient)
) {
  if (!query) return true;

  const fields = [
    patient.full_name,
    patient.username,
    patient.email,
    display.mrn,
    display.diagnosis,
    display.risk,
    display.attending,
    display.unit,
    patient.latest_status,
  ];

  return fields.some((field) => field?.toLowerCase().includes(query));
}

export default function PatientsPage() {
  const { user } = useAuthStore();
  const [patients, setPatients] = useState<RegistryPatient[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [searchQuery, setSearchQuery] = useState("");
  const [lastSyncTime, setLastSyncTime] = useState("");
  const [filtersOpen, setFiltersOpen] = useState(false);
  const [riskFilter, setRiskFilter] = useState<RiskFilter>("ALL");
  const [admissionPanelOpen, setAdmissionPanelOpen] = useState(false);

  useEffect(() => {
    setLoading(true);
    setError("");

    if (user?.role !== "admin" && user?.role !== "doctor") {
      setError("Unauthorized access. Medical staff privileges required.");
      setLoading(false);
      return;
    }

    const registryRequest = user.role === "doctor"
      ? getDoctorPatients().then((items) => items.map(doctorSummaryToRegistryPatient))
      : getAdminPatients().then((items) => items.map(adminUserToRegistryPatient));

    registryRequest
      .then((patientList) => {
        setPatients(patientList);
        setLastSyncTime(new Date().toLocaleTimeString());
      })
      .catch((err) => setError(err.message || "Failed to load patient records"))
      .finally(() => setLoading(false));
  }, [user]);

  if (error) {
    return (
      <div className="w-full max-w-4xl mx-auto text-center mt-20" role="alert">
        <ShieldAlert size={56} className="mx-auto mb-4 opacity-50 text-[var(--danger)]" aria-hidden="true" />
        <h1 className="text-xl font-bold text-[var(--text-primary)] mb-1">Access Denied</h1>
        <p className="text-xs text-[var(--text-secondary)] font-mono">{error}</p>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="w-full flex justify-center mt-20" role="status" aria-label="Loading patient records">
        <span className="w-8 h-8 border-2 border-[var(--accent)] border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  const normalizedSearchQuery = searchQuery.trim().toLowerCase();
  const filteredPatients = patients.filter((patient) => {
    const display = registryDisplayForPatient(patient);
    const matchesRisk = riskFilter === "ALL" || display.risk === riskFilter;
    return matchesRisk && patientMatchesSearch(patient, normalizedSearchQuery, display);
  });

  return (
    <div className="w-full space-y-6 pb-12 selection:bg-[var(--accent)] selection:text-white">
      {/* Registry ribbon */}
      <div className="glass-card px-4 py-2 flex flex-col md:flex-row md:items-center md:justify-between gap-2 font-mono text-[10px] tracking-wider text-[var(--text-dim)] uppercase" role="status" aria-label="Registry sync status">
        <div className="flex flex-wrap items-center gap-x-4 gap-y-1.5">
          <span className="flex items-center gap-1.5 text-[var(--accent)] font-semibold">
            <span className="w-1.5 h-1.5 rounded-full bg-[var(--accent)]" aria-hidden="true" /> FHIR REGISTRY SYNC
          </span>
          <span>MASTER PATIENT INDEX (MPI)</span>
        </div>
        <div className="flex flex-wrap items-center gap-x-4 gap-y-1.5">
          <span>LAST SYNC: {lastSyncTime}</span>
        </div>
      </div>

      <motion.div 
        initial={{ opacity: 0, y: -8 }} 
        animate={{ opacity: 1, y: 0 }} 
        transition={{ duration: 0.25 }} 
        className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-[var(--border)]"
      >
        <div>
          <h1 className="text-xl font-bold text-[var(--text-primary)] uppercase tracking-wider flex items-baseline gap-2">
            Patient Registry 
            <span className="text-[10px] bg-[rgba(255,255,255,0.03)] border border-[var(--border)] px-2 py-0.5 rounded text-[var(--text-secondary)] uppercase tracking-wider font-mono">
              Census: {filteredPatients.length}
            </span>
          </h1>
          <p className="text-xs text-[var(--text-secondary)] font-mono uppercase tracking-wide mt-1">EMR / Telemetry / Longitudinal Data</p>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <div className="relative">
            <Search size={13} className="absolute left-3 top-1/2 -translate-y-1/2 text-[var(--text-dim)]" aria-hidden="true" />
            <input
              type="text"
              placeholder="Search MRN, name, unit..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="input-clinical pl-9 w-full md:w-64"
              aria-label="Search patient records"
            />
          </div>
          <button
            className={`btn btn-secondary text-xs flex items-center justify-center gap-1.5 ${filtersOpen || riskFilter !== "ALL" ? "border-[var(--accent-border)] text-[var(--accent)] bg-[var(--accent-muted)]" : ""}`}
            aria-label="Filter patients"
            aria-expanded={filtersOpen}
            onClick={() => setFiltersOpen((open) => !open)}
          >
            <Filter size={13} aria-hidden="true" /> Filter
          </button>
          <button
            type="button"
            className="btn btn-primary text-xs flex items-center justify-center gap-1.5"
            aria-label="New patient admission"
            aria-expanded={admissionPanelOpen}
            onClick={() => setAdmissionPanelOpen((open) => !open)}
          >
            <Users size={13} aria-hidden="true" /> New Admission
          </button>
        </div>
      </motion.div>

      {filtersOpen && (
        <div className="panel p-3 flex flex-wrap items-center gap-2" role="region" aria-label="Patient registry filters">
          <span className="section-label mr-2">Risk Stratification</span>
          {RISK_FILTERS.map((filter) => (
            <button
              key={filter}
              type="button"
              aria-pressed={riskFilter === filter}
              onClick={() => setRiskFilter(filter)}
              className={`px-2.5 py-1 rounded border text-[10px] font-bold uppercase tracking-wider transition-colors cursor-pointer ${
                riskFilter === filter
                  ? "bg-[var(--accent-muted)] border-[var(--accent-border)] text-[var(--accent)]"
                  : "bg-[rgba(255,255,255,0.02)] border-[var(--border)] text-[var(--text-secondary)] hover:text-[var(--text-primary)]"
              }`}
            >
              {filter}
            </button>
          ))}
        </div>
      )}

      {admissionPanelOpen && (
        <section className="panel overflow-hidden" role="region" aria-label="New admission patient selection">
          <div className="panel-header flex justify-between items-center bg-[rgba(15,15,17,0.5)]">
            <div>
              <div className="section-label mb-1 flex items-center gap-1.5 text-[var(--accent)]">
                <Users size={12} aria-hidden="true" />
                Admission Workflow
              </div>
              <h2 className="text-sm font-bold text-[var(--text-primary)] uppercase">Select Patient for Onboarding</h2>
            </div>
            <div className="status-badge status-badge-accent">
              {filteredPatients.length} records available
            </div>
          </div>

          {filteredPatients.length > 0 ? (
            <div className="divide-y divide-[var(--border-subtle)]">
              {filteredPatients.map((patient) => {
                const display = registryDisplayForPatient(patient);
                const patientLabel = patient.full_name || patient.username;

                return (
                  <div key={patient.id} className="flex flex-col gap-3 p-4 md:flex-row md:items-center md:justify-between hover:bg-[rgba(255,255,255,0.01)] transition-colors">
                    <div className="min-w-0">
                      <div className="flex items-center gap-2">
                        <h3 className="text-xs font-bold text-[var(--text-primary)] uppercase">{patientLabel}</h3>
                        <span className="mono-meta text-[10px]">{display.mrn}</span>
                      </div>
                      <div className="mt-1 flex flex-wrap gap-x-4 gap-y-0.5 text-[10px] font-mono text-[var(--text-secondary)] uppercase">
                        <span>Unit: {display.unit}</span>
                        <span>Status: {patient.latest_status || "None"}</span>
                        <span>Admissions: {patient.active_admissions ?? 0}</span>
                        <span>Orders: {patient.open_orders ?? 0}</span>
                      </div>
                    </div>
                    <Link
                      to={`/patients/${patient.id}?intent=admission`}
                      aria-label={`Start admission for ${patientLabel}`}
                      className="btn btn-primary text-xs py-1.5 px-3 flex items-center justify-center gap-1"
                    >
                      Start Admission
                      <ChevronRight size={13} aria-hidden="true" />
                    </Link>
                  </div>
                );
              })}
            </div>
          ) : (
            <div className="p-4 text-xs font-mono text-[var(--text-dim)] uppercase tracking-wide">
              No matching patient records available.
            </div>
          )}
        </section>
      )}

      {/* Dense Clinical Table */}
      <div className="panel overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse" aria-label="Patient registry table">
            <thead className="text-[10px] font-bold uppercase tracking-wider bg-[rgba(15,15,17,0.85)] text-[var(--text-dim)] border-b border-[var(--border)]">
              <tr>
                <th className="px-4 py-3 border-r border-[var(--border)] w-12 text-center" scope="col">Status</th>
                <th className="px-4 py-3 border-r border-[var(--border)]" scope="col">Identifier (MRN)</th>
                <th className="px-4 py-3 border-r border-[var(--border)]" scope="col">Demographics</th>
                <th className="px-4 py-3 border-r border-[var(--border)]" scope="col">Diagnosis (ICD-10)</th>
                <th className="px-4 py-3 border-r border-[var(--border)]" scope="col">Acuity</th>
                <th className="px-4 py-3 border-r border-[var(--border)]" scope="col">Attending physician</th>
                <th className="px-4 py-3 text-right" scope="col">Actions</th>
              </tr>
            </thead>
            <tbody className="text-xs font-mono">
              {filteredPatients.length > 0 ? (
                filteredPatients.map((p) => {
                  const display = registryDisplayForPatient(p);

                  return (
                    <tr key={p.id} className="border-b border-[var(--border)] hover:bg-[rgba(255,255,255,0.015)] transition-colors group">
                      {/* Status Dot */}
                      <td className="px-4 py-3 border-r border-[var(--border)] text-center">
                        <div
                          className={`w-1.5 h-1.5 rounded-full mx-auto ${
                            display.isHighRisk
                              ? 'bg-[var(--danger)] shadow-[0_0_8px_rgba(239,68,68,0.5)]'
                              : display.risk === 'REVIEW'
                                ? 'bg-[var(--warning)] shadow-[0_0_8px_rgba(245,158,11,0.5)]'
                                : 'bg-[var(--success)] shadow-[0_0_8px_rgba(16,185,129,0.5)]'
                          }`}
                          aria-label={display.isHighRisk ? "High acuity" : display.risk === "REVIEW" ? "Acuity review needed" : "Normal acuity"}
                        />
                      </td>

                      {/* Patient Identifier */}
                      <td className="px-4 py-3 border-r border-[var(--border)]">
                        <div className="font-sans font-bold text-[var(--text-primary)] text-[12px] uppercase">{p.full_name || p.username}</div>
                        <div className="text-[var(--text-dim)] mt-0.5">{display.mrn}</div>
                        {display.isHighRisk && (
                          <div className="inline-flex mt-1 bg-[var(--danger-muted)] border border-[var(--danger-border)] text-[var(--danger)] text-[9px] px-1 py-0.5 uppercase tracking-wider font-bold">
                            High Alert
                          </div>
                        )}
                      </td>

                      {/* Demographics */}
                      <td className="px-4 py-3 border-r border-[var(--border)] text-[var(--text-secondary)] uppercase">
                        <div>DOB: {display.dob}{display.age !== null ? ` (${display.age}Y)` : ""}</div>
                        <div className="mt-0.5 text-[var(--text-dim)]">Sex: {p.gender || "None"} | Blood: {p.blood_type || "None"}</div>
                      </td>

                      {/* Primary Diagnosis */}
                      <td className="px-4 py-3 border-r border-[var(--border)]">
                        <div className="text-[var(--text-primary)] uppercase">{display.diagnosis}</div>
                        <div className="text-[var(--text-dim)] mt-0.5 flex items-center gap-1">
                          <Activity size={10} aria-hidden="true" /> {display.telemetryStatus}
                        </div>
                      </td>

                      {/* Risk Stratification */}
                      <td className="px-4 py-3 border-r border-[var(--border)]">
                        <div className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded-sm border text-[10px] font-bold ${
                          display.risk === 'CRITICAL' ? 'bg-[var(--danger-muted)] border-[var(--danger-border)] text-[var(--danger)]' :
                          display.risk === 'HIGH' ? 'bg-[var(--warning-muted)] border-[var(--warning-border)] text-[var(--warning)]' :
                          display.risk === 'REVIEW' ? 'bg-[var(--warning-muted)] border-[var(--warning-border)] text-[var(--warning)]' :
                          display.risk === 'MODERATE' ? 'bg-[var(--accent-muted)] border-[var(--accent-border)] text-[var(--accent)]' :
                          'bg-[var(--success-muted)] border-[var(--success-border)] text-[var(--success)]'
                        }`}>
                          {(display.isHighRisk || display.risk === "REVIEW") && <AlertTriangle size={10} aria-hidden="true" />}
                          {display.risk}
                        </div>
                      </td>

                      {/* Attending / Unit */}
                      <td className="px-4 py-3 border-r border-[var(--border)] text-[var(--text-secondary)] uppercase">
                        <div className="flex items-center gap-1"><Stethoscope size={11} className="text-[var(--text-dim)]" aria-hidden="true" /> Attending: {display.attending}</div>
                        <div className="mt-0.5">{display.unit}</div>
                        {p.latest_status && <div className="mt-0.5 text-[var(--text-dim)]">Status: {p.latest_status}</div>}
                      </td>

                      {/* Actions */}
                      <td className="px-4 py-3 text-right align-middle">
                        <Link to={`/patients/${p.id}`}>
                          <button className="p-1 bg-[rgba(255,255,255,0.03)] border border-[var(--border)] hover:bg-[var(--accent)] hover:border-[var(--accent)] hover:text-white transition-colors rounded cursor-pointer" aria-label={`View record for ${p.full_name || p.username}`}>
                            <ChevronRight size={14} aria-hidden="true" />
                          </button>
                        </Link>
                      </td>
                    </tr>
                  );
                })
              ) : (
                <tr>
                  <td colSpan={7} className="px-4 py-8 text-center text-[var(--text-dim)] uppercase tracking-wide">
                    No matching patient records found in registry
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
        <div className="p-3 border-t border-[var(--border)] bg-[rgba(15,15,17,0.5)] section-label text-right">
          Showing {filteredPatients.length > 0 ? 1 : 0}-{filteredPatients.length} of {filteredPatients.length} records
        </div>
      </div>
    </div>
  );
}
