"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { getAdminUsers, type UserProfile } from "@/lib/api";
import { useAuthStore } from "@/lib/auth";
import { motion } from "framer-motion";
import { Users, Search, Filter, ShieldAlert, FileText, CheckCircle2, Activity, AlertTriangle, ChevronRight, Stethoscope } from "lucide-react";

export default function PatientsPage() {
  const { user } = useAuthStore();
  const [patients, setPatients] = useState<UserProfile[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [searchQuery, setSearchQuery] = useState("");

  useEffect(() => {
    // Only admins or doctors should access this
    if (user?.role !== "admin" && user?.role !== "doctor") {
      setError("Unauthorized access. Medical staff privileges required.");
      setLoading(false);
      return;
    }

    getAdminUsers()
      .then((usersData) => {
        const patientList = usersData.filter(u => u.role !== 'admin');
        setPatients(patientList);
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

  const filteredPatients = patients.filter(p => 
    p.full_name?.toLowerCase().includes(searchQuery.toLowerCase()) || 
    p.username.toLowerCase().includes(searchQuery.toLowerCase()) ||
    p.email.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="w-full min-h-screen bg-[var(--bg-primary)] text-[var(--text-primary)] font-sans selection:bg-[var(--accent)] selection:text-white pb-20">
      {/* Top Status Bar - FHIR/HL7 Mock */}
      <div className="w-full bg-[var(--bg-secondary)] border-b border-[var(--border)] px-4 py-1.5 flex justify-between items-center text-[11px] font-mono tracking-widest text-[var(--text-dim)] uppercase" role="status" aria-label="Registry sync status">
        <div className="flex gap-4">
          <span className="flex items-center gap-1.5 text-[var(--accent)]"><div className="w-1.5 h-1.5 bg-[var(--accent)] rounded-full" aria-hidden="true" /> FHIR REGISTRY SYNC</span>
          <span>MASTER PATIENT INDEX (MPI)</span>
        </div>
        <div className="flex gap-4">
          <span>LAST SYNC: {new Date().toLocaleTimeString()}</span>
        </div>
      </div>

      <div className="p-6 md:p-8 max-w-[1800px] mx-auto space-y-6">
        <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.3 }} className="flex flex-col md:flex-row md:items-end justify-between gap-4 pb-6 border-b border-[var(--border)]">
          <div>
            <h1 className="text-3xl font-semibold text-[var(--text-primary)] mb-1 tracking-tight flex items-center gap-3">
              Patient Registry <span className="text-[11px] bg-[var(--bg-card)] border border-[var(--border)] px-2 py-1 rounded text-[var(--text-secondary)] uppercase tracking-widest align-middle">CENSUS: {filteredPatients.length}</span>
            </h1>
            <p className="text-[var(--text-secondary)] text-sm font-mono mt-1">EMR / Telemetry / Longitudinal Data</p>
          </div>
          
          <div className="flex gap-3">
            <div className="relative">
              <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-[var(--text-dim)]" aria-hidden="true" />
              <input 
                type="text" 
                placeholder="Search MRN, Name, or ICD-10..." 
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="input-clinical pl-9 w-full md:w-80"
                aria-label="Search patient records"
              />
            </div>
            <button className="btn btn-secondary text-xs font-bold uppercase tracking-wider flex items-center justify-center gap-2" aria-label="Filter patients">
              <Filter size={14} aria-hidden="true" /> Filter
            </button>
            <button className="btn btn-primary text-xs font-bold uppercase tracking-wider flex items-center justify-center gap-2" aria-label="New patient admission">
              <Users size={14} aria-hidden="true" /> New Admission
            </button>
          </div>
        </motion.div>

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
                  filteredPatients.map((p, i) => {
                    // Simulated clinical data points for the dense look
                    const mrn = `MRN-${(p.id * 1024 + 100000).toString().substring(0,6)}`;
                    const riskLevels = ["LOW", "MODERATE", "HIGH", "CRITICAL"];
                    const riskIdx = (p.id * 7) % 4;
                    const risk = riskLevels[riskIdx];
                    const isHighRisk = risk === "HIGH" || risk === "CRITICAL";
                    
                    const icdCodes = ["I10 (Hypertension)", "E11.9 (Type 2 DM)", "J44.9 (COPD)", "N18.9 (CKD)", "I50.9 (Heart Failure)"];
                    const diagnosis = icdCodes[(p.id * 3) % icdCodes.length];

                    const units = ["ICU-A", "MED-SURG", "CARDIOLOGY", "OUTPATIENT"];
                    const unit = units[(p.id * 5) % units.length];

                    return (
                      <tr key={p.id} className="border-b border-[var(--border)] hover:bg-[var(--bg-card)] transition-colors group">
                        {/* Status Marker */}
                        <td className="px-4 py-3 border-r border-[var(--border)] text-center bg-[var(--bg-primary)]">
                          <div className={`w-2 h-2 rounded-full mx-auto ${isHighRisk ? 'bg-[var(--danger)]' : 'bg-[var(--success)]'}`} aria-label={isHighRisk ? "High risk" : "Normal risk"} />
                        </td>

                        {/* Patient Identifier */}
                        <td className="px-4 py-3 border-r border-[var(--border)]">
                          <div className="font-sans font-bold text-[var(--text-primary)] text-[13px]">{p.full_name || p.username}</div>
                          <div className="text-[var(--text-secondary)] mt-0.5">{mrn}</div>
                          {isHighRisk && <div className="inline-flex mt-1 bg-[var(--danger-muted)] border border-[var(--danger-border)] text-[var(--danger)] text-[9px] px-1 py-0.5 uppercase tracking-widest">Acuity: Level 1</div>}
                        </td>

                        {/* Demographics / Contact */}
                        <td className="px-4 py-3 border-r border-[var(--border)] text-[var(--text-secondary)]">
                          <div>DOB: {p.dob || '1985-04-12'} ({Math.floor(Math.random()*40 + 30)}Y)</div>
                          <div className="mt-0.5 text-[var(--text-dim)]">Sex: {p.gender || 'M'} | Blood: {p.blood_type || 'O+'}</div>
                        </td>

                        {/* Primary Diagnosis */}
                        <td className="px-4 py-3 border-r border-[var(--border)]">
                          <div className="text-[var(--text-primary)]">{diagnosis}</div>
                          <div className="text-[var(--text-dim)] mt-0.5 flex items-center gap-1">
                            <Activity size={10} aria-hidden="true" /> Last telemetry: {Math.floor(Math.random() * 24)}h ago
                          </div>
                        </td>

                        {/* Risk Stratification */}
                        <td className="px-4 py-3 border-r border-[var(--border)]">
                          <div className={`inline-flex items-center gap-1.5 px-2 py-1 border ${
                            risk === 'CRITICAL' ? 'bg-[var(--danger-muted)] border-[var(--danger-border)] text-[var(--danger)]' :
                            risk === 'HIGH' ? 'bg-[var(--warning-muted)] border-[var(--warning)]/30 text-[var(--warning)]' :
                            risk === 'MODERATE' ? 'bg-[var(--accent-muted)] border-[var(--accent-border)] text-[var(--accent)]' :
                            'bg-[var(--success-muted)] border-[var(--success-border)] text-[var(--success)]'
                          }`}>
                            {isHighRisk && <AlertTriangle size={12} aria-hidden="true" />}
                            {risk}
                          </div>
                        </td>

                        {/* Attending / Unit */}
                        <td className="px-4 py-3 border-r border-[var(--border)] text-[var(--text-secondary)]">
                          <div className="flex items-center gap-1.5"><Stethoscope size={12} className="text-[var(--text-dim)]" aria-hidden="true" /> Dr. Smith</div>
                          <div className="mt-0.5">{unit}</div>
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
            SHOWING 1-{filteredPatients.length} OF {filteredPatients.length} ENTRIES
          </div>
        </div>
      </div>
    </div>
  );
}
