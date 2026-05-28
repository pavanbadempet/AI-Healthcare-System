"use client";

import { use, useEffect, useState } from "react";
import { useAuthStore } from "@/lib/auth";
import { exportDoctorPatientFhirBundle, getAdminPatient, getDoctorPatients, type DoctorPatientSummary, type UserProfile } from "@/lib/api";
import { ChevronLeft, FileDigit, BrainCircuit, Loader2, ShieldAlert } from "lucide-react";
import Link from "next/link";
import PatientCareActions from "@/components/operations/PatientCareActions";
import PatientCareTimeline from "@/components/operations/PatientCareTimeline";
import PatientDiagnosticResults from "@/components/operations/PatientDiagnosticResults";
import PatientDiagnosticsReview from "@/components/operations/PatientDiagnosticsReview";
import PatientMedicationsPanel from "@/components/operations/PatientMedicationsPanel";
import PatientMonitoringSignals from "@/components/operations/PatientMonitoringSignals";

interface PatientIdentity {
  fullName: string;
  username: string;
  dob?: string;
  gender?: string;
  bloodType?: string;
}

interface PatientSearchParams {
  intent?: string | string[];
}

const EMPTY_SEARCH_PARAMS = Promise.resolve({});
const RECORD_UNAVAILABLE_MESSAGE = "This patient record is not available for the current account.";

function doctorSummaryToIdentity(summary: DoctorPatientSummary): PatientIdentity {
  return {
    fullName: summary.full_name || summary.username,
    username: summary.username,
  };
}

function userProfileToIdentity(profile: UserProfile): PatientIdentity {
  return {
    fullName: profile.full_name || profile.username,
    username: profile.username,
    dob: profile.dob,
    gender: profile.gender,
    bloodType: profile.blood_type,
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

function firstSearchParam(value?: string | string[]) {
  return Array.isArray(value) ? value[0] : value;
}

export default function PatientEMRView({
  params,
  searchParams = EMPTY_SEARCH_PARAMS,
}: {
  params: Promise<{ id: string }>;
  searchParams?: Promise<PatientSearchParams>;
}) {
  const resolvedParams = use(params);
  const resolvedSearchParams = use(searchParams);
  const { user } = useAuthStore();
  const patientId = Number.parseInt(resolvedParams.id, 10);
  const workflowIntent = firstSearchParam(resolvedSearchParams.intent);
  const [mounted, setMounted] = useState(false);
  const [patientIdentity, setPatientIdentity] = useState<PatientIdentity | null>(null);
  const [identityLoading, setIdentityLoading] = useState(true);
  const [recordAccessError, setRecordAccessError] = useState("");
  const [exportMessage, setExportMessage] = useState("");
  const [exportError, setExportError] = useState("");
  const [exportingBundle, setExportingBundle] = useState(false);
  const [aiReviewMessage, setAiReviewMessage] = useState("");

  useEffect(() => {
    setMounted(true);
  }, []);

  useEffect(() => {
    let active = true;
    setPatientIdentity(null);
    setRecordAccessError("");
    setIdentityLoading(true);

    async function loadPatientIdentity() {
      try {
        if (!Number.isFinite(patientId) || patientId <= 0) {
          if (active) setRecordAccessError("Invalid patient record.");
          return;
        }

        if (!user) {
          if (active) setRecordAccessError(RECORD_UNAVAILABLE_MESSAGE);
          return;
        }

        if (user?.role === "doctor") {
          const summaries = await getDoctorPatients();
          const summary = summaries.find((item) => item.patient_id === patientId);
          if (active) {
            if (summary) {
              setPatientIdentity(doctorSummaryToIdentity(summary));
            } else {
              setRecordAccessError(RECORD_UNAVAILABLE_MESSAGE);
            }
          }
          return;
        }

        if (user?.role === "admin") {
          try {
            const profile = await getAdminPatient(patientId);
            if (active) setPatientIdentity(userProfileToIdentity(profile));
          } catch (err) {
            if (!active) return;
            const message = err instanceof Error ? err.message : "";
            setRecordAccessError(message === "Patient not found" ? RECORD_UNAVAILABLE_MESSAGE : "Unable to verify patient record access.");
          }
          return;
        }

        if (user?.role === "patient") {
          if (active) {
            if (user.id === patientId) {
              setPatientIdentity(userProfileToIdentity(user));
            } else {
              setRecordAccessError(RECORD_UNAVAILABLE_MESSAGE);
            }
          }
          return;
        }

        if (active) setRecordAccessError(RECORD_UNAVAILABLE_MESSAGE);
      } catch {
        if (active) setRecordAccessError("Unable to verify patient record access.");
      } finally {
        if (active) setIdentityLoading(false);
      }
    }

    void loadPatientIdentity();

    return () => {
      active = false;
    };
  }, [patientId, user]);

  useEffect(() => {
    if (!mounted || workflowIntent !== "admission") return;

    const scrollToWorkflow = () => {
      document.getElementById("admission-workflow-status")?.scrollIntoView?.({ block: "start", behavior: "auto" });
    };

    if (typeof window.requestAnimationFrame === "function") {
      window.requestAnimationFrame(scrollToWorkflow);
    } else {
      scrollToWorkflow();
    }
  }, [mounted, workflowIntent]);

  if (!mounted) return null;

  if (identityLoading) {
    return (
      <div className="w-full flex justify-center mt-20" role="status" aria-label="Loading patient record access">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-[var(--accent)]" />
      </div>
    );
  }

  if (recordAccessError) {
    return (
      <div className="w-full max-w-4xl mx-auto text-center mt-20 px-6" role="alert">
        <ShieldAlert size={56} className="mx-auto mb-6 opacity-60 text-[var(--warning)]" aria-hidden="true" />
        <h1 className="text-2xl font-bold text-[var(--text-primary)] mb-2">Patient Record Unavailable</h1>
        <p className="text-[var(--text-secondary)]">{recordAccessError}</p>
        <Link href="/patients" className="btn btn-secondary mt-6 inline-flex">
          Back to Registry
        </Link>
      </div>
    );
  }

  const mrn = `MRN-${(patientId * 1024 + 100000).toString().substring(0,6)}`;
  const patientName = patientIdentity?.fullName || patientIdentity?.username || `Patient #${Number.isFinite(patientId) ? patientId : "Unknown"}`;
  const patientDob = patientIdentity?.dob || "Not recorded";
  const patientAge = patientIdentity?.dob ? calculateAge(patientIdentity.dob) : null;
  const patientSex = patientIdentity?.gender?.toUpperCase() || "Not recorded";
  const patientBloodType = patientIdentity?.bloodType || "Not recorded";
  const canExportFhirBundle = user?.role === "doctor";
  const canPrepareAiReview = user?.role === "doctor";

  async function handleExportFhirBundle() {
    setExportMessage("");
    setExportError("");

    if (!Number.isFinite(patientId) || patientId <= 0) {
      setExportError("Cannot export an invalid patient record");
      return;
    }

    setExportingBundle(true);
    try {
      const payload = await exportDoctorPatientFhirBundle(patientId);
      const signatureAlgorithm = payload.manifest.signature_algorithm || "signed manifest";
      setExportMessage(
        `FHIR bundle export #${payload.export.id} prepared (${payload.export.resource_count} resources). Manifest: ${signatureAlgorithm}.`
      );
    } catch (err) {
      setExportError(err instanceof Error ? err.message : "Failed to prepare FHIR bundle export");
    } finally {
      setExportingBundle(false);
    }
  }

  function handlePrepareAiReview() {
    setAiReviewMessage("Verified source data is required before clinician-reviewed AI synthesis can be prepared.");
    document.getElementById("clinical-ai-synthesis")?.scrollIntoView?.({ block: "start", behavior: "smooth" });
  }

  return (
    <div className="w-full min-h-screen bg-[var(--bg-primary)] text-[var(--text-primary)] font-sans selection:bg-[var(--accent)] selection:text-white pb-20">
      {/* Top Status Bar */}
      <div className="w-full bg-[var(--warning-muted)] border-b border-[var(--warning)]/25 px-4 py-2 flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between text-[11px] font-bold font-mono tracking-widest text-[var(--warning)] uppercase" role="status" aria-label="Patient safety context">
        <div className="flex flex-wrap gap-x-4 gap-y-1">
          <span className="flex items-center gap-1.5"><AlertPulse /> ACUITY: Review source systems</span>
          <span>LOCATION: Not assigned</span>
        </div>
        <div className="flex flex-wrap gap-x-4 gap-y-1">
          <span>CODE STATUS: Not recorded</span>
          <span>ALLERGIES: Not recorded</span>
        </div>
      </div>

      <div className="p-6 md:p-8 max-w-[1800px] mx-auto space-y-6">
        {/* Header */}
        <header className="flex flex-col md:flex-row md:items-start justify-between gap-6 pb-6 border-b border-[var(--border)]">
          <div>
            <Link href="/patients" className="inline-flex items-center gap-2 text-[var(--text-dim)] hover:text-[var(--text-primary)] text-[11px] uppercase tracking-widest font-bold mb-4 transition-colors">
              <ChevronLeft size={14} aria-hidden="true" /> Back to Registry
            </Link>
            <h1 className="text-3xl font-semibold text-[var(--text-primary)] tracking-tight mb-2 flex flex-wrap items-baseline gap-x-2">
              {patientName} <span className="text-[var(--text-secondary)] font-mono text-sm whitespace-nowrap">{mrn}</span>
            </h1>
            <p className="text-[var(--text-secondary)] text-sm font-mono flex flex-wrap items-center gap-x-4 gap-y-2">
              <span className="whitespace-nowrap">DOB: {patientDob}{patientAge !== null ? ` (${patientAge}Y)` : ""}</span>
              <span className="whitespace-nowrap">SEX: {patientSex}</span>
              <span className="whitespace-nowrap">BLOOD: {patientBloodType}</span>
            </p>
          </div>
          <div className="flex flex-col gap-2 md:items-end">
            <div className="flex flex-wrap gap-3">
              {canExportFhirBundle && (
                <button
                  className="btn btn-secondary text-xs font-semibold uppercase tracking-wider flex items-center gap-2"
                  aria-label="Export FHIR Bundle"
                  disabled={exportingBundle}
                  onClick={handleExportFhirBundle}
                >
                  {exportingBundle ? <Loader2 size={14} className="animate-spin" aria-hidden="true" /> : <FileDigit size={14} aria-hidden="true" />}
                  Export FHIR Bundle
                </button>
              )}
              {canPrepareAiReview && (
                <button
                  className="btn btn-primary text-xs font-semibold uppercase tracking-wider flex items-center gap-2"
                  aria-label="Prepare clinician-reviewed AI analysis"
                  onClick={handlePrepareAiReview}
                >
                  <BrainCircuit size={14} aria-hidden="true" /> Prepare AI Review
                </button>
              )}
            </div>
            {exportMessage && (
              <div className="max-w-xl rounded border border-[var(--success-border)] bg-[var(--success-muted)] px-3 py-2 text-xs text-[var(--success)]" role="status">
                {exportMessage}
              </div>
            )}
            {exportError && (
              <div className="max-w-xl rounded border border-[var(--danger-border)] bg-[var(--danger-muted)] px-3 py-2 text-xs text-[var(--danger)]" role="alert">
                {exportError}
              </div>
            )}
          </div>
        </header>

        {workflowIntent === "admission" && (
          <div id="admission-workflow-status" className="scroll-mt-24 rounded-md border border-[var(--accent-border)] bg-[var(--accent-muted)] px-4 py-3 text-sm text-[var(--accent)]" role="status">
            <strong>Admission workflow selected.</strong> Open a clinician-reviewed encounter before creating an admission.
          </div>
        )}
        <div id="care-workflow-actions">
          <PatientCareActions patientId={patientId} />
        </div>
        <PatientMonitoringSignals patientId={patientId} />
        <PatientDiagnosticsReview patientId={patientId} />
        <PatientDiagnosticResults patientId={patientId} />
        <PatientCareTimeline patientId={patientId} />

        <div className="grid grid-cols-1 xl:grid-cols-4 gap-6">
          {/* Left Column: Vitals & Labs */}
          <div className="xl:col-span-1 space-y-6">
            <div className="panel p-5" role="region" aria-label="Live vital signs telemetry">
              <h3 className="section-label mb-4">Live Telemetry</h3>
              <div className="rounded-md border border-[var(--border)] bg-[var(--bg-card)] p-4 text-sm leading-6 text-[var(--text-secondary)]">
                No verified live telemetry loaded from source systems for this patient record.
              </div>
            </div>

            <div className="panel p-5" role="region" aria-label="Latest laboratory results">
              <h3 className="section-label mb-4">Latest Labs</h3>
              <div className="rounded-md border border-[var(--border)] bg-[var(--bg-card)] p-4 text-sm leading-6 text-[var(--text-secondary)]">
                No verified laboratory results loaded from source systems for this patient record.
              </div>
            </div>
          </div>

          {/* Middle Column: Active Problems & Notes */}
          <div className="xl:col-span-2 space-y-6">
            <div className="panel p-5" role="region" aria-label="Active problem list">
              <h3 className="section-label mb-4">Active Problem List</h3>
              <div className="rounded-md border border-[var(--border)] bg-[var(--bg-card)] p-4 text-sm leading-6 text-[var(--text-secondary)]">
                No verified active problems loaded from source systems for this patient record.
              </div>
            </div>

            <div id="clinical-ai-synthesis" className="panel p-5 h-full min-h-[300px]" role="region" aria-label="Clinical AI synthesis">
              <h3 className="section-label mb-4">Clinical AI Synthesis</h3>
              {aiReviewMessage && (
                <div className="mb-4 rounded-md border border-[var(--warning)]/30 bg-[var(--warning-muted)] px-3 py-2 text-xs font-semibold text-[var(--warning)]" role="alert">
                  {aiReviewMessage}
                </div>
              )}
              <div className="prose prose-invert prose-sm max-w-none text-[var(--text-secondary)]">
                <p>
                  <strong>AI DRAFT SIGNALS:</strong><br />
                  No clinician-reviewed AI synthesis prepared for this patient record in this session.
                </p>
                <p>
                  <strong>CLINICIAN REVIEW CHECKLIST:</strong><br />
                  1. Load verified vitals, labs, medications, imaging, and allergies from source systems.<br />
                  2. Ask the clinician to prepare or review AI-generated draft signals only after source data is present.<br />
                  3. Document the clinician&apos;s independent assessment before treatment decisions.
                </p>
                <p className="text-[var(--warning)]">
                  Decision support only: this AI draft is not a diagnosis or treatment plan. Patients should consult a qualified clinician for diagnosis or treatment, and emergencies require immediate hospital emergency workflow escalation.
                </p>
              </div>
            </div>
          </div>

          {/* Right Column: Imaging and Medications */}
          <div className="xl:col-span-1 space-y-6">
            <div className="bg-[var(--bg-primary)] border border-[var(--border)] p-0 flex flex-col h-[400px]" role="region" aria-label="PACS DICOM viewer">
              <div className="px-4 py-3 border-b border-[var(--border)] flex justify-between items-center bg-[var(--bg-secondary)]">
                <h3 className="section-label">PACS / DICOM Viewer</h3>
                <span className="text-[11px] bg-[var(--bg-card)] border border-[var(--border)] px-2 py-0.5 rounded text-[var(--text-primary)]">No study selected</span>
              </div>
              <div className="flex-1 relative flex items-center justify-center bg-[var(--bg-card)] overflow-hidden p-4 text-center text-[var(--text-dim)] font-mono text-xs leading-6">
                No imaging study loaded from PACS for this patient record.
              </div>
              <div className="px-4 py-2 border-t border-[var(--border)] bg-[var(--bg-secondary)] flex justify-between mono-meta">
                <span>Viewer idle</span>
                <span>Awaiting source data</span>
              </div>
            </div>

            <PatientMedicationsPanel patientId={patientId} />
          </div>
        </div>
      </div>
    </div>
  );
}

function AlertPulse() {
  return (
    <div className="relative flex h-2 w-2" aria-hidden="true">
      <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-[var(--warning)] opacity-75"></span>
      <span className="relative inline-flex rounded-full h-2 w-2 bg-[var(--warning)]"></span>
    </div>
  );
}
