"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
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

    // Only admins or doctors should access this
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
        <ShieldAlert size={64} className="mx-auto mb-6 opacity-50 text-[var(--danger)]" aria-hidden="true" />
        <h1 className="text-2xl font-bold text-[var(--text-primary)] mb-2">Access Denied</h1>
        <p className="text-[var(--text-secondary)]">{error}</p>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="w-full flex justify-center mt-20" role="status" aria-label="Loading patient records">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-[var(--accent)]" />
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
    <div className="w-full space-y-6 pb-10 selection:bg-[var(--accent)] selection:text-black">
      {/* Registry ribbon */}
      <div className="glass-card px-4 py-2 flex flex-col md:flex-row md:items-center md:justify-between gap-2 font-mono text-[11px] tracking-[0.18em] text-[var(--text-dim)] uppercase" role="status" aria-label="Registry sync status">
        <div className="flex flex-wrap items-center gap-x-4 gap-y-2">
          <span className="flex items-center gap-2 text-[var(--accent)]">
            <span className="w-1.5 h-1.5 rounded-sm bg-[var(--accent)]" aria-hidden="true" /> FHIR REGISTRY SYNC
          </span>
          <span>MASTER PATIENT INDEX (MPI)</span>
        </div>
        <div className="flex flex-wrap items-center gap-x-4 gap-y-2">
          <span>LAST SYNC: {lastSyncTime}</span>
        </div>
      </div>

        <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.3 }} className="flex flex-col md:flex-row md:items-end justify-between gap-4 pb-6 border-b border-[var(--border)]">
          <div>
            <h1 className="text-3xl md:text-5xl text-[var(--text-primary)] mb-2 flex items-center gap-3 display-hero">
              Patient Registry <span className="text-[11px] bg-[var(--bg-card)] border border-[var(--border)] px-2 py-1 rounded text-[var(--text-secondary)] uppercase tracking-widest align-middle">CENSUS: {filteredPatients.length}</span>
            </h1>
            <p className="lede text-sm font-mono mt-1">EMR / Telemetry / Longitudinal Data</p>
          </div>

          <div className="grid w-full grid-cols-2 gap-3 md:flex md:w-auto">
            <div className="relative col-span-2 md:col-span-1">
              <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-[var(--text-dim)]" aria-hidden="true" />
              <input
                type="text"
                placeholder="Search MRN, name, unit, or status..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="input-clinical pl-9 w-full md:w-80"
                aria-label="Search patient records"
              />
            </div>
            <button
              className={`btn btn-secondary text-xs font-bold uppercase tracking-wider flex items-center justify-center gap-2 ${filtersOpen || riskFilter !== "ALL" ? "border-[var(--accent-border)] text-[var(--accent)]" : ""}`}
              aria-label="Filter patients"
              aria-expanded={filtersOpen}
              onClick={() => setFiltersOpen((open) => !open)}
            >
              <Filter size={14} aria-hidden="true" /> Filter
            </button>
            <button
              type="button"
              className="btn btn-primary text-xs font-bold uppercase tracking-wider flex items-center justify-center gap-2"
              aria-label="New patient admission"
              aria-expanded={admissionPanelOpen}
              onClick={() => setAdmissionPanelOpen((open) => !open)}
            >
              <Users size={14} aria-hidden="true" /> New Admission
            </button>
          </div>
        </motion.div>

        {filtersOpen && (
          <div className="panel p-3 flex flex-wrap items-center gap-2" role="region" aria-label="Patient registry filters">
            <span className="section-label mr-2">Risk</span>
            {RISK_FILTERS.map((filter) => (
              <button
                key={filter}
                type="button"
                aria-pressed={riskFilter === filter}
                onClick={() => setRiskFilter(filter)}
                className={`px-3 py-1.5 rounded border text-[11px] font-bold uppercase tracking-wider transition-colors ${
                  riskFilter === filter
                    ? "bg-[var(--accent-muted)] border-[var(--accent-border)] text-[var(--accent)]"
                    : "bg-[var(--bg-secondary)] border-[var(--border)] text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:border-[var(--border-focus)]"
                }`}
              >
                {filter}
              </button>
            ))}
          </div>
        )}

        {admissionPanelOpen && (
          <section className="panel overflow-hidden" role="region" aria-label="New admission patient selection">
            <div className="panel-header flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
              <div>
                <div className="section-label mb-2 flex items-center gap-2 text-[var(--accent)]">
                  <Users size={13} aria-hidden="true" />
                  Admission Worklist
                </div>
                <h2 className="text-xl font-semibold text-[var(--text-primary)]">Select Patient for Admission</h2>
              </div>
              <div className="status-badge status-badge-accent">
                {filteredPatients.length} eligible {filteredPatients.length === 1 ? "record" : "records"}
              </div>
            </div>

            {filteredPatients.length > 0 ? (
              <div className="divide-y divide-[var(--border)]">
                {filteredPatients.map((patient) => {
                  const display = registryDisplayForPatient(patient);
                  const patientLabel = patient.full_name || patient.username;

                  return (
                    <div key={patient.id} className="flex flex-col gap-4 p-4 md:flex-row md:items-center md:justify-between">
                      <div className="min-w-0">
                        <div className="flex flex-wrap items-center gap-2">
                          <h3 className="text-sm font-semibold text-[var(--text-primary)]">{patientLabel}</h3>
                          <span className="mono-meta">{display.mrn}</span>
                        </div>
                        <div className="mt-2 flex flex-wrap gap-x-4 gap-y-1 text-xs text-[var(--text-secondary)]">
                          <span>Unit: {display.unit}</span>
                          <span>Status: {patient.latest_status || "Not recorded"}</span>
                          <span>Active admissions: {patient.active_admissions ?? 0}</span>
                          <span>Open orders: {patient.open_orders ?? 0}</span>
                        </div>
                      </div>
                      <Link
                        href={`/patients/${patient.id}?intent=admission`}
                        aria-label={`Start admission for ${patientLabel}`}
                        className="btn btn-primary text-xs font-bold uppercase tracking-wider flex items-center justify-center gap-2"
                      >
                        Start Admission
                        <ChevronRight size={14} aria-hidden="true" />
                      </Link>
                    </div>
                  );
                })}
              </div>
            ) : (
              <div className="p-5 text-sm text-[var(--text-secondary)]">
                No matching patient records available for admission workflow.
              </div>
            )}
          </section>
        )}

        {/* Dense Clinical Table */}
        <div className="panel">
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse" aria-label="Patient registry table">
              <thead className="text-[11px] font-bold uppercase tracking-widest bg-[var(--bg-card)] text-[var(--text-dim)] border-b border-[var(--border)]">
                <tr>
                  <th className="px-4 py-3 border-r border-[var(--border)] w-12 text-center" scope="col">STS</th>
                  <th className="px-4 py-3 border-r border-[var(--border)]" scope="col">Patient Identifier (MRN)</th>
                  <th className="px-4 py-3 border-r border-[var(--border)]" scope="col">Demographics / Contact</th>
                  <th className="px-4 py-3 border-r border-[var(--border)]" scope="col">Primary Diagnosis (ICD-10)</th>
                  <th className="px-4 py-3 border-r border-[var(--border)]" scope="col">Risk Stratification</th>
                  <th className="px-4 py-3 border-r border-[var(--border)]" scope="col">Attending / Unit</th>
                  <th className="px-4 py-3 text-right" scope="col">Actions</th>
                </tr>
              </thead>
              <tbody className="text-[12px] font-mono">
                {filteredPatients.length > 0 ? (
                  filteredPatients.map((p) => {
                    const display = registryDisplayForPatient(p);

                    return (
                      <tr key={p.id} className="border-b border-[var(--border)] hover:bg-[var(--bg-card)] transition-colors group">
                        {/* Status Marker */}
                        <td className="px-4 py-3 border-r border-[var(--border)] text-center bg-[var(--bg-primary)]">
                          <div
                            className={`w-2 h-2 rounded-full mx-auto ${
                              display.isHighRisk
                                ? 'bg-[var(--danger)]'
                                : display.risk === 'REVIEW'
                                  ? 'bg-[var(--warning)]'
                                  : 'bg-[var(--success)]'
                            }`}
                            aria-label={display.isHighRisk ? "High risk" : display.risk === "REVIEW" ? "Clinical risk review required" : "Normal risk"}
                          />
                        </td>

                        {/* Patient Identifier */}
                        <td className="px-4 py-3 border-r border-[var(--border)]">
                          <div className="font-sans font-bold text-[var(--text-primary)] text-[13px]">{p.full_name || p.username}</div>
                          <div className="text-[var(--text-secondary)] mt-0.5">{display.mrn}</div>
                          {display.isHighRisk && <div className="inline-flex mt-1 bg-[var(--danger-muted)] border border-[var(--danger-border)] text-[var(--danger)] text-[9px] px-1 py-0.5 uppercase tracking-widest">Acuity: Level 1</div>}
                        </td>

                        {/* Demographics / Contact */}
                        <td className="px-4 py-3 border-r border-[var(--border)] text-[var(--text-secondary)]">
                          <div>DOB: {display.dob}{display.age !== null ? ` (${display.age}Y)` : ""}</div>
                          <div className="mt-0.5 text-[var(--text-dim)]">Sex: {p.gender || "Not recorded"} | Blood: {p.blood_type || "Not recorded"}</div>
                        </td>

                        {/* Primary Diagnosis */}
                        <td className="px-4 py-3 border-r border-[var(--border)]">
                          <div className="text-[var(--text-primary)]">{display.diagnosis}</div>
                          <div className="text-[var(--text-dim)] mt-0.5 flex items-center gap-1">
                            <Activity size={10} aria-hidden="true" /> {display.telemetryStatus}
                          </div>
                        </td>

                        {/* Risk Stratification */}
                        <td className="px-4 py-3 border-r border-[var(--border)]">
                          <div className={`inline-flex items-center gap-1.5 px-2 py-1 border ${
                            display.risk === 'CRITICAL' ? 'bg-[var(--danger-muted)] border-[var(--danger-border)] text-[var(--danger)]' :
                            display.risk === 'HIGH' ? 'bg-[var(--warning-muted)] border-[var(--warning)]/30 text-[var(--warning)]' :
                            display.risk === 'REVIEW' ? 'bg-[var(--warning-muted)] border-[var(--warning)]/30 text-[var(--warning)]' :
                            display.risk === 'MODERATE' ? 'bg-[var(--accent-muted)] border-[var(--accent-border)] text-[var(--accent)]' :
                            'bg-[var(--success-muted)] border-[var(--success-border)] text-[var(--success)]'
                          }`}>
                            {(display.isHighRisk || display.risk === "REVIEW") && <AlertTriangle size={12} aria-hidden="true" />}
                            {display.risk}
                          </div>
                        </td>

                        {/* Attending / Unit */}
                        <td className="px-4 py-3 border-r border-[var(--border)] text-[var(--text-secondary)]">
                          <div className="flex items-center gap-1.5"><Stethoscope size={12} className="text-[var(--text-dim)]" aria-hidden="true" /> Attending: {display.attending}</div>
                          <div className="mt-0.5">{display.unit}</div>
                          {p.latest_status && <div className="mt-0.5 text-[var(--text-dim)]">Status: {p.latest_status}</div>}
                        </td>

                        {/* Actions */}
                        <td className="px-4 py-3 text-right align-middle bg-[var(--bg-primary)] group-hover:bg-[var(--bg-card)]">
                          <Link href={`/patients/${p.id}`}>
                            <button className="p-1.5 bg-[var(--bg-secondary)] border border-[var(--border)] hover:bg-[var(--accent)] hover:border-[var(--accent)] hover:text-[var(--text-primary)] text-[var(--text-secondary)] transition-colors rounded" aria-label={`View record for ${p.full_name || p.username}`}>
                              <ChevronRight size={16} aria-hidden="true" />
                            </button>
                          </Link>
                        </td>
                      </tr>
                    );
                  })
                ) : (
                  <tr>
                    <td colSpan={7} className="px-5 py-12 text-center text-[var(--text-dim)] bg-[var(--bg-primary)]">
                      NO MATCHING PATIENT RECORDS FOUND IN REGISTRY
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
          <div className="p-3 border-t border-[var(--border)] bg-[var(--bg-primary)] section-label text-right">
            SHOWING {filteredPatients.length > 0 ? 1 : 0}-{filteredPatients.length} OF {filteredPatients.length} ENTRIES
          </div>
        </div>
    </div>
  );
}
