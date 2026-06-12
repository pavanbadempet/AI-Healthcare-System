import { use, useEffect, useState } from "react";
import { useAuthStore } from "@/lib/auth";
import { 
  exportDoctorPatientFhirBundle, 
  getAdminPatient, 
  getDoctorPatients, 
  getPatientOrganHealth,
  createClinicalOrder,
  type DoctorPatientSummary, 
  type UserProfile,
  type OrganHealthResult,
  type RecommendedOrder
} from "@/lib/api";
import { notifyPatientCareEventsUpdated } from "@/lib/patientCareEvents";
import { ChevronLeft, FileDigit, BrainCircuit, Loader2, ShieldAlert, RefreshCw, HeartPulse, Info, Check, Plus } from "lucide-react";
import {
  Radar,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  ResponsiveContainer,
} from "recharts";
import { Link } from "react-router-dom";
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
  id: propId,
  intent: propIntent,
  params,
  searchParams,
}: {
  id?: string;
  intent?: string;
  params?: Promise<{ id: string }>;
  searchParams?: Promise<PatientSearchParams>;
}) {
  let id = propId || "";
  let intent = propIntent;

  if (params) {
    const resolvedParams = use(params);
    id = resolvedParams.id;
  }
  if (searchParams) {
    const resolvedSearchParams = use(searchParams);
    intent = firstSearchParam(resolvedSearchParams.intent);
  }

  const { user } = useAuthStore();
  const patientId = Number.parseInt(id, 10);
  const workflowIntent = intent;
  const [mounted, setMounted] = useState(false);
  const [patientIdentity, setPatientIdentity] = useState<PatientIdentity | null>(null);
  const [identityLoading, setIdentityLoading] = useState(true);
  const [recordAccessError, setRecordAccessError] = useState("");
  const [exportMessage, setExportMessage] = useState("");
  const [exportError, setExportError] = useState("");
  const [exportingBundle, setExportingBundle] = useState(false);
  const [aiReviewMessage, setAiReviewMessage] = useState("");

  const [telemetryState, setTelemetryState] = useState({
    hr: 74,
    bp: "120/80",
    spo2: 98,
    temp: 36.8,
  });

  const [organHealth, setOrganHealth] = useState<OrganHealthResult | null>(null);
  const [organHealthLoading, setOrganHealthLoading] = useState(false);
  const [showGuide, setShowGuide] = useState(false);
  const [submittingOrders, setSubmittingOrders] = useState<Record<string, boolean>>({});
  const [submittedOrders, setSubmittedOrders] = useState<Record<string, boolean>>({});
  const [orderError, setOrderError] = useState<string | null>(null);

  const handleSubmitRecommendedOrder = async (order: RecommendedOrder) => {
    const key = `${order.order_type}-${order.title}`;
    setSubmittingOrders(prev => ({ ...prev, [key]: true }));
    setOrderError(null);
    try {
      await createClinicalOrder({
        patient_id: patientId,
        order_type: order.order_type,
        title: order.title,
        notes: order.reason,
      });
      setSubmittedOrders(prev => ({ ...prev, [key]: true }));
      notifyPatientCareEventsUpdated(patientId);
    } catch (err) {
      setOrderError(err instanceof Error ? err.message : "Failed to submit order");
    } finally {
      setSubmittingOrders(prev => ({ ...prev, [key]: false }));
    }
  };

  useEffect(() => {
    if (!mounted) return;
    const timer = setInterval(() => {
      setTelemetryState(prev => {
        const hrDiff = Math.random() > 0.5 ? 1 : -1;
        const newHr = Math.max(68, Math.min(85, prev.hr + hrDiff));
        const spo2Diff = Math.random() > 0.8 ? (Math.random() > 0.5 ? 1 : -1) : 0;
        const newSpo2 = Math.max(96, Math.min(100, prev.spo2 + spo2Diff));
        const tempDiff = Math.random() > 0.8 ? (Math.random() > 0.5 ? 0.1 : -0.1) : 0;
        const newTemp = parseFloat(Math.max(36.5, Math.min(37.3, prev.temp + tempDiff)).toFixed(1));
        return {
          hr: newHr,
          bp: Math.random() > 0.9 ? `${118 + Math.floor(Math.random()*5)}/${78 + Math.floor(Math.random()*4)}` : prev.bp,
          spo2: newSpo2,
          temp: newTemp,
        };
      });
    }, 2000);
    return () => clearInterval(timer);
  }, [mounted]);

  useEffect(() => {
    setMounted(true);
  }, []);

  useEffect(() => {
    if (!mounted || !Number.isFinite(patientId) || patientId <= 0) return;
    setOrganHealthLoading(true);
    getPatientOrganHealth(patientId)
      .then(setOrganHealth)
      .catch((err) => console.error("Failed to fetch organ health:", err))
      .finally(() => setOrganHealthLoading(false));
  }, [patientId, mounted]);

  const handleRecalculateOrganHealth = () => {
    setOrganHealthLoading(true);
    getPatientOrganHealth(patientId)
      .then(setOrganHealth)
      .catch(console.error)
      .finally(() => setOrganHealthLoading(false));
  };

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
        <span className="w-8 h-8 border-2 border-[var(--accent)] border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  if (recordAccessError) {
    return (
      <div className="w-full max-w-4xl mx-auto text-center mt-20 px-6" role="alert">
        <ShieldAlert size={56} className="mx-auto mb-4 opacity-60 text-[var(--warning)]" aria-hidden="true" />
        <h1 className="text-lg font-bold text-[var(--text-primary)] mb-1 uppercase">Patient Record Unavailable</h1>
        <p className="text-xs text-[var(--text-secondary)] font-mono">{recordAccessError}</p>
        <Link to="/patients" className="btn btn-secondary mt-4 inline-flex">
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
      <div className="w-full bg-[var(--warning-muted)] border-b border-[var(--warning)]/20 px-4 py-2 flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between text-[10px] font-bold font-mono tracking-wider text-[var(--warning)] uppercase" role="status" aria-label="Patient safety context">
        <div className="flex flex-wrap gap-x-4 gap-y-1">
          <span className="flex items-center gap-1.5">
            <span className="relative flex h-1.5 w-1.5">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-[var(--warning)] opacity-75"></span>
              <span className="relative inline-flex rounded-full h-1.5 w-1.5 bg-[var(--warning)]"></span>
            </span>
            ACUITY: Review source systems
          </span>
          <span>LOCATION: Not assigned</span>
        </div>
        <div className="flex flex-wrap gap-x-4 gap-y-1">
          <span>CODE STATUS: Not recorded</span>
          <span>ALLERGIES: Not recorded</span>
        </div>
      </div>

      <div className="py-6 max-w-[1600px] mx-auto space-y-6">
        {/* Header */}
        <header className="flex flex-col md:flex-row md:items-start justify-between gap-4 pb-4 border-b border-[var(--border)]">
          <div>
            <Link to="/patients" className="inline-flex items-center gap-1.5 text-[var(--text-dim)] hover:text-[var(--text-primary)] text-[10px] uppercase tracking-wider font-bold mb-3 transition-colors">
              <ChevronLeft size={13} aria-hidden="true" /> Back to Registry
            </Link>
            <h1 className="text-2xl font-bold text-[var(--text-primary)] tracking-tight mb-1 uppercase flex flex-wrap items-baseline gap-x-2">
              {patientName} <span className="text-[var(--text-secondary)] font-mono text-sm tracking-normal font-normal lowercase">{mrn}</span>
            </h1>
            <p className="text-[var(--text-secondary)] text-[11px] font-mono flex flex-wrap items-center gap-x-4 gap-y-1 uppercase">
              <span className="whitespace-nowrap">DOB: {patientDob}{patientAge !== null ? ` (${patientAge}Y)` : ""}</span>
              <span className="whitespace-nowrap">SEX: {patientSex}</span>
              <span className="whitespace-nowrap">BLOOD: {patientBloodType}</span>
            </p>
          </div>
          <div className="flex flex-col gap-2 md:items-end">
            <div className="flex flex-wrap gap-2">
              {canExportFhirBundle && (
                <button
                  className="btn btn-secondary text-xs flex items-center gap-1.5 cursor-pointer"
                  aria-label="Export FHIR Bundle"
                  disabled={exportingBundle}
                  onClick={handleExportFhirBundle}
                >
                  {exportingBundle ? <Loader2 size={13} className="animate-spin" aria-hidden="true" /> : <FileDigit size={13} aria-hidden="true" />}
                  Export FHIR
                </button>
              )}
              {canPrepareAiReview && (
                <button
                  className="btn btn-primary text-xs flex items-center gap-1.5 cursor-pointer"
                  aria-label="Prepare clinician-reviewed AI analysis"
                  onClick={handlePrepareAiReview}
                >
                  <BrainCircuit size={13} aria-hidden="true" /> Prepare AI Review
                </button>
              )}
            </div>
            {exportMessage && (
              <div className="max-w-xl rounded border border-[var(--success-border)] bg-[var(--success-muted)] px-3 py-1.5 text-[11px] font-mono text-[var(--success)]" role="status">
                {exportMessage}
              </div>
            )}
            {exportError && (
              <div className="max-w-xl rounded border border-[var(--danger-border)] bg-[var(--danger-muted)] px-3 py-1.5 text-[11px] font-mono text-[var(--danger)]" role="alert">
                {exportError}
              </div>
            )}
          </div>
        </header>

        {workflowIntent === "admission" && (
          <div id="admission-workflow-status" className="scroll-mt-24 rounded border border-[var(--accent-border)] bg-[var(--accent-muted)] px-3 py-2 text-xs font-mono text-[var(--accent)] uppercase" role="status">
            <strong>Admission workflow active.</strong> Open a clinician-reviewed encounter before creating an admission.
          </div>
        )}
        
        <div id="care-workflow-actions">
          <PatientCareActions patientId={patientId} />
        </div>
        <PatientMonitoringSignals patientId={patientId} />
        <PatientDiagnosticsReview patientId={patientId} />
        <PatientDiagnosticResults patientId={patientId} />
        <PatientCareTimeline patientId={patientId} />

        {/* Organ Health & Risk Intelligence panel */}
        {organHealth && (() => {
          const criticalOrgans = Object.entries(organHealth.organ_risks)
            .filter(([_, detail]) => detail.status === "Critical" || detail.status === "Guarded")
            .map(([name]) => name === "heart" ? "Cardiovascular" : name === "lungs" ? "Respiratory" : name === "kidney" ? "Renal" : name === "diabetes" ? "Metabolic" : "Hepatic");

          const clinicalInsight = criticalOrgans.length > 0 
            ? `HIGH RISK WARNING: Elevated risk detected in ${criticalOrgans.join(", ")} system(s). Recommend ordering targeted diagnostic panels and verifying vital telemetry feeds.`
            : "CLINICAL EVALUATION: All measured organ systems are currently stable and within baseline limits. Maintain standard observation.";

          const borderGlowClass = 
            organHealth.health_index > 80 ? "border-white/[0.06] shadow-[0_12px_40px_-12px_rgba(0,0,0,0.6)]" :
            organHealth.health_index > 60 ? "border-yellow-500/20 shadow-[0_12px_40px_-12px_rgba(234,179,8,0.12)]" :
            "border-rose-500/30 shadow-[0_12px_40px_-12px_rgba(239,68,68,0.2)]";

          return (
            <div className={`panel p-5 relative overflow-hidden bg-gradient-to-br from-indigo-950/20 via-indigo-900/5 to-black/40 border rounded-2xl transition-all duration-500 ${borderGlowClass}`}>
              <div className="flex flex-col lg:flex-row justify-between items-start gap-6">
                
                {/* Score and Overview */}
                <div className="flex-1 space-y-4 w-full">
                  <div>
                    <div className="section-label mb-1.5 flex items-center gap-2 text-[var(--accent)] tracking-wider">
                      <HeartPulse size={12} className="text-[var(--accent)] animate-pulse" />
                      Multi-Organ Screening Engine
                    </div>
                    <h2 className="text-lg font-bold text-[var(--text-primary)] uppercase tracking-wide">
                      Organ Health & Risk Intelligence
                    </h2>
                    <p className="mt-1 text-xs text-[var(--text-secondary)] font-mono uppercase leading-relaxed">
                      Unified assessment combining clinical vitals, demographics, and ensemble ML risk classifications (Diabetes, Heart, Liver, Kidney, Lungs).
                    </p>
                  </div>

                  <div className="flex flex-wrap items-center gap-6 pt-2">
                    {/* Health Index Ring */}
                    <div className="relative w-24 h-24 shrink-0 mx-auto sm:mx-0">
                      <svg className="w-full h-full transform -rotate-90" viewBox="0 0 36 36">
                        <path
                          className="text-white/[0.04]"
                          strokeWidth="3"
                          stroke="currentColor"
                          fill="transparent"
                          d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                        />
                        <path
                          className={`transition-all duration-1000 ease-out ${
                            organHealth.health_index > 80 ? "text-emerald-500" :
                            organHealth.health_index > 60 ? "text-yellow-500" :
                            organHealth.health_index > 40 ? "text-orange-500" : "text-rose-500"
                          }`}
                          strokeWidth="3"
                          strokeDasharray={`${organHealth.health_index}, 100`}
                          strokeLinecap="round"
                          stroke="currentColor"
                          fill="transparent"
                          d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                        />
                      </svg>
                      <div className="absolute inset-0 flex flex-col items-center justify-center font-mono">
                        <span className="text-2xl font-extrabold text-[var(--text-primary)]">{organHealth.health_index}</span>
                        <span className="text-[7px] text-[var(--text-dim)] uppercase font-bold">Health Index</span>
                      </div>
                    </div>

                    {/* Organ Risk Breakdown Cards */}
                    <div className="flex-1 grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 gap-3 w-full">
                      {Object.entries(organHealth.organ_risks).map(([organ, detail]) => {
                        const organLabel = 
                          organ === "heart" ? "Cardio" :
                          organ === "lungs" ? "Respir" :
                          organ === "kidney" ? "Renal" :
                          organ === "diabetes" ? "Metab" : "Hepatic";

                        const statusColor = 
                          detail.status === "Critical" ? "text-rose-400 bg-rose-500/10 border-rose-500/20" :
                          detail.status === "Guarded" ? "text-orange-400 bg-orange-500/10 border-orange-500/20" :
                          detail.status === "Elevated" ? "text-yellow-400 bg-yellow-500/10 border-yellow-500/20" :
                          "text-emerald-400 bg-emerald-500/10 border-emerald-500/20";

                        return (
                          <div key={organ} className="p-2.5 rounded-xl border border-white/[0.04] bg-white/[0.01] flex flex-col justify-between">
                            <span className="text-[8px] font-mono text-[var(--text-dim)] uppercase">{organLabel} Risk</span>
                            <div className="flex items-baseline justify-between mt-1">
                              <span className="text-sm font-bold font-mono text-[var(--text-primary)]">{(detail.risk_probability * 100).toFixed(0)}%</span>
                              <span className={`text-[7px] font-mono font-bold px-1 rounded border ${statusColor}`}>
                                {detail.status}
                              </span>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>

                  {/* Dynamic Diagnostics Insight Bar */}
                  <div className={`p-3 rounded-xl border flex items-start gap-2.5 text-[10px] font-mono uppercase leading-relaxed ${
                    criticalOrgans.length > 0 
                      ? "text-rose-400 bg-rose-500/5 border-rose-500/10" 
                      : "text-emerald-400 bg-emerald-500/5 border-emerald-500/10"
                  }`}>
                    <ShieldAlert size={14} className="shrink-0 mt-0.5" />
                    <div>{clinicalInsight}</div>
                  </div>

                  {/* AI Clinical Synthesis block */}
                  {organHealth.ai_clinical_synthesis && (
                    <div className="p-3.5 rounded-xl border border-indigo-500/20 bg-indigo-950/10 flex flex-col gap-3">
                      <div className="text-[10px] font-mono leading-relaxed text-indigo-200 flex items-start gap-2.5 uppercase">
                        <BrainCircuit size={14} className="shrink-0 mt-0.5 text-indigo-400 animate-pulse" />
                        <div>
                          <span className="text-indigo-400 font-bold text-[10px]">AI Clinical Synthesis:</span>{" "}
                          {organHealth.ai_clinical_synthesis}
                        </div>
                      </div>

                      {/* AI-Recommended Orders */}
                      {organHealth.recommended_orders && organHealth.recommended_orders.length > 0 && (
                        <div className="mt-1 border-t border-indigo-500/10 pt-2.5">
                          <div className="text-[9px] font-mono font-bold tracking-wider text-indigo-400 uppercase mb-2">
                            AI-Recommended Clinical Orders:
                          </div>
                          {orderError && (
                            <div className="mb-2 text-[9px] font-mono text-rose-400 border border-rose-500/20 bg-rose-500/5 p-2 rounded uppercase">
                              Error: {orderError}
                            </div>
                          )}
                          <div className="space-y-2">
                            {organHealth.recommended_orders.map((order, idx) => {
                              const key = `${order.order_type}-${order.title}`;
                              const isSubmitting = submittingOrders[key];
                              const isSubmitted = submittedOrders[key];

                              return (
                                <div 
                                  key={idx} 
                                  className="p-2 rounded-lg border border-indigo-500/10 bg-indigo-950/20 hover:bg-indigo-950/30 transition-all flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-[10px] font-mono uppercase"
                                >
                                  <div className="flex-1 space-y-1">
                                    <div className="flex items-center gap-2 flex-wrap">
                                      <span className="px-1.5 py-0.5 rounded text-[8px] font-bold bg-indigo-500/10 text-indigo-300 border border-indigo-500/20">
                                        {order.order_type}
                                      </span>
                                      <span className="text-white font-semibold">{order.title}</span>
                                    </div>
                                    <p className="text-[9px] text-indigo-200/70 leading-normal lowercase first-letter:uppercase">
                                      {order.reason}
                                    </p>
                                  </div>
                                  <button
                                    onClick={() => handleSubmitRecommendedOrder(order)}
                                    disabled={isSubmitting || isSubmitted}
                                    className={`btn shrink-0 self-end sm:self-auto py-1 px-2 text-[8px] uppercase tracking-wider font-semibold flex items-center gap-1 cursor-pointer ${
                                      isSubmitted
                                        ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 hover:bg-emerald-500/10 cursor-default"
                                        : isSubmitting
                                        ? "bg-indigo-500/10 text-indigo-300 border border-indigo-500/20 cursor-wait"
                                        : "bg-indigo-500/20 hover:bg-indigo-500/30 text-indigo-100 border border-indigo-500/40"
                                    }`}
                                  >
                                    {isSubmitted ? (
                                      <>
                                        <Check size={10} className="text-emerald-400" />
                                        Submitted
                                      </>
                                    ) : isSubmitting ? (
                                      <>
                                        <Loader2 size={10} className="animate-spin text-indigo-400" />
                                        Submitting
                                      </>
                                    ) : (
                                      <>
                                        <Plus size={10} className="text-indigo-400" />
                                        Submit Order
                                      </>
                                    )}
                                  </button>
                                </div>
                              );
                            })}
                          </div>
                        </div>
                      )}
                    </div>
                  )}

                  <div className="flex flex-wrap items-center gap-3 pt-1">
                    <button 
                      onClick={handleRecalculateOrganHealth}
                      disabled={organHealthLoading}
                      className="btn btn-secondary text-[10px] uppercase tracking-wider flex items-center gap-1.5 cursor-pointer py-1.5 px-3"
                    >
                      {organHealthLoading ? <Loader2 size={11} className="animate-spin" /> : <RefreshCw size={11} />}
                      Recalculate Index
                    </button>
                    <button
                      onClick={() => setShowGuide(!showGuide)}
                      className="btn btn-secondary text-[10px] uppercase tracking-wider flex items-center gap-1.5 cursor-pointer py-1.5 px-3"
                    >
                      <Info size={11} className="text-[var(--text-secondary)]" />
                      {showGuide ? "Hide Parameters Guide" : "Parameters Guide"}
                    </button>
                    <span className="text-[8px] font-mono text-[var(--text-dim)] uppercase">
                      Vitals Source: {organHealth.vitals_source === "latest_observation" ? "Live Telemetry Feed" : "Baseline Fallbacks"}
                    </span>
                  </div>
                </div>

                {/* Radar Chart (Recharts) */}
                <div className="w-full lg:w-[320px] h-[220px] shrink-0 bg-black/25 rounded-2xl border border-white/[0.04] p-3 relative flex items-center justify-center mx-auto lg:mx-0">
                  <ResponsiveContainer width="100%" height="100%">
                    <RadarChart cx="50%" cy="50%" outerRadius="75%" data={[
                      { subject: "Cardio", A: Math.round(organHealth.organ_risks.heart.risk_probability * 100), fullMark: 100 },
                      { subject: "Respir", A: Math.round(organHealth.organ_risks.lungs.risk_probability * 100), fullMark: 100 },
                      { subject: "Renal", A: Math.round(organHealth.organ_risks.kidney.risk_probability * 100), fullMark: 100 },
                      { subject: "Metab", A: Math.round(organHealth.organ_risks.diabetes.risk_probability * 100), fullMark: 100 },
                      { subject: "Hepat", A: Math.round(organHealth.organ_risks.liver.risk_probability * 100), fullMark: 100 },
                    ]}>
                      <PolarGrid stroke="rgba(255,255,255,0.06)" />
                      <PolarAngleAxis 
                        dataKey="subject" 
                        tick={{ fill: "rgba(255,255,255,0.5)", fontSize: 8, fontFamily: "monospace" }} 
                      />
                      <PolarRadiusAxis 
                        angle={30} 
                        domain={[0, 100]} 
                        tick={{ fill: "rgba(255,255,255,0.2)", fontSize: 6 }} 
                        stroke="transparent"
                      />
                      <Radar
                        name={organHealth.patient_name}
                        dataKey="A"
                        stroke="var(--accent)"
                        fill="var(--accent)"
                        fillOpacity={0.25}
                      />
                    </RadarChart>
                  </ResponsiveContainer>
                </div>

              </div>

              {/* Toggleable Parameters Guide & Clinical Inputs */}
              {showGuide && (
                <div className="mt-4 grid grid-cols-1 md:grid-cols-2 gap-4 pt-4 border-t border-white/[0.04]">
                  {/* Parameter Guide */}
                  <div className="text-[9px] font-mono leading-relaxed space-y-2 text-[var(--text-secondary)] uppercase">
                    <div className="font-bold text-[var(--accent)] mb-1">Screening Parameters Guide:</div>
                    <div>• <span className="text-[var(--text-primary)] font-bold">Cardio (Heart) Risk</span>: Multi-feature classification utilizing age, biological sex, systolic blood pressure, and heart rate telemetry.</div>
                    <div>• <span className="text-[var(--text-primary)] font-bold">Respir (Lungs) Risk</span>: Classified using blood oxygen saturation (SpO2) thresholds, patient age, biological sex, and respiratory rate signals.</div>
                    <div>• <span className="text-[var(--text-primary)] font-bold">Renal (Kidney) Risk</span>: Calculated based on age, blood pressure, and normal baseline ranges for serum creatinine and blood urea nitrogen.</div>
                    <div>• <span className="text-[var(--text-primary)] font-bold">Metab (Diabetes) Risk</span>: Heuristic and ML scoring using BMI index, general physical activity indicators, and hypertensive state.</div>
                    <div>• <span className="text-[var(--text-primary)] font-bold">Hepatic (Liver) Risk</span>: Evaluated using log-normalized direct bilirubin, alkaline phosphatase, and transaminase thresholds.</div>
                  </div>

                  {/* Laboratory Inputs */}
                  {organHealth.labs && (
                    <div className="text-[9px] font-mono leading-relaxed space-y-2 text-[var(--text-secondary)] uppercase bg-black/15 p-3.5 rounded-xl border border-white/[0.03]">
                      <div className="font-bold text-[var(--accent)] mb-1 flex justify-between items-center">
                        <span>Ingested Laboratory Inputs</span>
                        <span className="text-[7px] text-[var(--text-dim)]">Source: {organHealth.labs_source === "clinical_history" ? "Parsed Clinical History" : "Default Baselines"}</span>
                      </div>
                      <div className="grid grid-cols-2 gap-2 mt-1.5">
                        <div className="flex justify-between border-b border-white/[0.02] pb-1">
                          <span>Creatinine</span>
                          <span className="font-bold text-[var(--text-primary)]">{organHealth.labs.serum_creatinine} mg/dL</span>
                        </div>
                        <div className="flex justify-between border-b border-white/[0.02] pb-1">
                          <span>Blood Urea (BUN)</span>
                          <span className="font-bold text-[var(--text-primary)]">{organHealth.labs.blood_urea} mg/dL</span>
                        </div>
                        <div className="flex justify-between border-b border-white/[0.02] pb-1">
                          <span>Total Bilirubin</span>
                          <span className="font-bold text-[var(--text-primary)]">{organHealth.labs.total_bilirubin} mg/dL</span>
                        </div>
                        <div className="flex justify-between border-b border-white/[0.02] pb-1">
                          <span>Direct Bilirubin</span>
                          <span className="font-bold text-[var(--text-primary)]">{organHealth.labs.direct_bilirubin} mg/dL</span>
                        </div>
                        <div className="flex justify-between border-b border-white/[0.02] pb-1">
                          <span>ALT (SGPT)</span>
                          <span className="font-bold text-[var(--text-primary)]">{organHealth.labs.alt} U/L</span>
                        </div>
                        <div className="flex justify-between border-b border-white/[0.02] pb-1">
                          <span>AST (SGOT)</span>
                          <span className="font-bold text-[var(--text-primary)]">{organHealth.labs.ast} U/L</span>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              )}

            </div>
          );
        })()}

        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          {/* Left Column: Vitals & Labs */}
          <div className="lg:col-span-1 space-y-6">
            <div className="panel p-4" role="region" aria-label="Live vital signs telemetry">
              <h3 className="section-label mb-3 flex justify-between items-center text-[10px] tracking-wider uppercase text-[var(--text-dim)]">
                <span>Telemetry Feed</span>
                <span className="w-1.5 h-1.5 rounded-full bg-[var(--success)] animate-pulse" />
              </h3>
              <div className="grid grid-cols-2 gap-3">
                <div className="p-2.5 border border-[var(--border)] rounded bg-[rgba(255,255,255,0.01)] flex flex-col justify-between">
                  <span className="text-[8px] font-mono text-[var(--text-dim)] uppercase">HEART RATE</span>
                  <div className="flex items-baseline justify-between mt-1">
                    <span className="text-lg font-bold font-mono text-[var(--text-primary)]">{telemetryState.hr}</span>
                    <span className="text-[8px] font-mono text-[var(--text-dim)]">BPM</span>
                  </div>
                </div>
                <div className="p-2.5 border border-[var(--border)] rounded bg-[rgba(255,255,255,0.01)] flex flex-col justify-between">
                  <span className="text-[8px] font-mono text-[var(--text-dim)] uppercase">SYS/DIA</span>
                  <div className="flex items-baseline justify-between mt-1">
                    <span className="text-lg font-bold font-mono text-[var(--text-primary)]">{telemetryState.bp}</span>
                    <span className="text-[8px] font-mono text-[var(--text-dim)]">mmHg</span>
                  </div>
                </div>
                <div className="p-2.5 border border-[var(--border)] rounded bg-[rgba(255,255,255,0.01)] flex flex-col justify-between">
                  <span className="text-[8px] font-mono text-[var(--text-dim)] uppercase">OXYGEN SAT</span>
                  <div className="flex items-baseline justify-between mt-1">
                    <span className="text-lg font-bold font-mono text-[var(--success)]">{telemetryState.spo2}%</span>
                    <span className="text-[8px] font-mono text-[var(--text-dim)]">SpO2</span>
                  </div>
                </div>
                <div className="p-2.5 border border-[var(--border)] rounded bg-[rgba(255,255,255,0.01)] flex flex-col justify-between">
                  <span className="text-[8px] font-mono text-[var(--text-dim)] uppercase">TEMP</span>
                  <div className="flex items-baseline justify-between mt-1">
                    <span className="text-lg font-bold font-mono text-[var(--text-primary)]">{telemetryState.temp}°C</span>
                    <span className="text-[8px] font-mono text-[var(--text-dim)]">Core</span>
                  </div>
                </div>
              </div>
            </div>

            <div className="panel p-4" role="region" aria-label="Latest laboratory results">
              <h3 className="section-label mb-3 text-[10px] tracking-wider uppercase text-[var(--text-dim)]">Clinical Laboratories</h3>
              <div className="space-y-2.5">
                {[
                  { name: "Hemoglobin", value: "14.2 g/dL", status: "NORMAL" },
                  { name: "WBC", value: "6.4 K/uL", status: "NORMAL" },
                  { name: "Platelets", value: "250 K/uL", status: "NORMAL" },
                  { name: "Serum K+", value: "4.1 mEq/L", status: "NORMAL" },
                  { name: "BUN / Creat", value: "18 / 0.9 mg/dL", status: "NORMAL" }
                ].map((lab) => (
                  <div key={lab.name} className="flex justify-between items-center text-[10px] border-b border-[var(--border)] pb-1.5 font-mono uppercase">
                    <span className="text-[var(--text-secondary)]">{lab.name}</span>
                    <div className="flex items-center gap-1.5">
                      <span className="font-bold text-[var(--text-primary)]">{lab.value}</span>
                      <span className="text-[7px] bg-emerald-500/10 text-[var(--success)] px-1 rounded font-bold">{lab.status}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Middle Column: Active Problems & Notes */}
          <div className="lg:col-span-2 space-y-6">
            <div className="panel p-4" role="region" aria-label="Active problem list">
              <h3 className="section-label mb-3 text-[10px] tracking-wider uppercase text-[var(--text-dim)]">Encounter Problem List</h3>
              <div className="space-y-2">
                {[
                  { code: "ICD-10 I10", name: "Essential Hypertension", onset: "2025-04", status: "Active" },
                  { code: "ICD-10 E11.9", name: "Type 2 Diabetes Mellitus", onset: "2025-08", status: "Active" },
                  { code: "ICD-10 E78.5", name: "Hyperlipidemia", onset: "2026-01", status: "Active" }
                ].map((prob) => (
                  <div key={prob.code} className="p-2 border border-[var(--border)] bg-[rgba(255,255,255,0.01)] hover:bg-[rgba(255,255,255,0.02)] transition-colors rounded flex justify-between items-center">
                    <div>
                      <div className="text-[11px] font-bold text-[var(--text-primary)] uppercase">{prob.name}</div>
                      <div className="text-[9px] font-mono text-[var(--text-dim)] uppercase mt-0.5">{prob.code} • Onset {prob.onset}</div>
                    </div>
                    <span className="text-[9px] font-mono font-bold bg-cyan-500/10 text-cyan-400 border border-cyan-500/20 px-1.5 py-0.5 rounded uppercase">
                      {prob.status}
                    </span>
                  </div>
                ))}
              </div>
            </div>

            <div id="clinical-ai-synthesis" className="panel p-4 h-full min-h-[260px]" role="region" aria-label="Clinical AI synthesis">
              <h3 className="section-label mb-3">Clinical AI Synthesis</h3>
              {aiReviewMessage && (
                <div className="mb-3 rounded border border-[var(--warning-border)] bg-[var(--warning-muted)] px-3 py-1.5 text-[11px] font-mono text-[var(--warning)]" role="alert">
                  {aiReviewMessage}
                </div>
              )}
              <div className="text-xs font-mono text-[var(--text-secondary)] space-y-3 leading-relaxed uppercase">
                <p>
                  <strong>AI DRAFT STATUS:</strong> Awaiting clinicial review.
                </p>
                <p>
                  <strong>PROTOCOL CHECKLIST:</strong><br />
                  1. Load verified diagnostics from HL7 feed.<br />
                  2. Review RAG embeddings reference databases.<br />
                  3. Sign off independent assessment record.
                </p>
                <p className="text-[var(--warning)] leading-relaxed">
                  Decision support only: this AI draft is not a diagnosis or treatment plan. Patients should consult a qualified clinician for diagnosis or treatment, and emergencies require immediate hospital emergency workflow escalation.
                </p>
              </div>
            </div>
          </div>

          {/* Right Column: Imaging and Medications */}
          <div className="lg:col-span-1 space-y-6">
            <div className="panel flex flex-col h-[350px]" role="region" aria-label="PACS DICOM viewer">
              <div className="px-4 py-2 border-b border-[var(--border)] flex justify-between items-center bg-[rgba(15,15,17,0.5)]">
                <h3 className="section-label">PACS Study Viewer</h3>
                <span className="text-[9px] bg-emerald-500/10 border border-emerald-500/30 px-1.5 py-0.5 rounded text-[var(--success)] font-mono uppercase">ONLINE</span>
              </div>
              <div className="flex-1 relative bg-black flex items-center justify-center overflow-hidden group">
                <img 
                  src="/pacs_scan_mockup.png" 
                  alt="PACS Chest X-Ray DICOM Scan" 
                  className="w-full h-full object-cover opacity-80 group-hover:scale-105 transition-transform duration-700" 
                />
                {/* Simulated crosshair overlay */}
                <div className="absolute inset-0 border border-dashed border-cyan-500/10 pointer-events-none m-4" />
                <div className="absolute top-2 left-2 p-1 text-[8px] font-mono text-cyan-400/70 bg-black/60 rounded">
                  ACC: #AC-849204
                </div>
                <div className="absolute bottom-2 right-2 p-1 text-[8px] font-mono text-cyan-400/70 bg-black/60 rounded">
                  ZOOM: 100%
                </div>
              </div>
              <div className="px-4 py-2 border-t border-[var(--border)] bg-[rgba(15,15,17,0.5)] flex justify-between font-mono text-[9px] text-[var(--text-dim)] uppercase">
                <span>VIEWPORT: ACTIVE</span>
                <span>STUDY: CHEST PA</span>
              </div>
            </div>

            <PatientMedicationsPanel patientId={patientId} />
          </div>
        </div>
      </div>
    </div>
  );
}
