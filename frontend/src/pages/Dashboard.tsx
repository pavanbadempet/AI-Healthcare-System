import { useEffect, useState, useMemo, useRef, lazy } from "react";
import { useAuthStore } from "@/lib/auth";
import {
  getRecords,
  getDemoReadiness,
  getAdminPatients,
  getDoctorPatients,
  type HealthRecord,
} from "@/lib/api";
import { useTelemetry } from "@/lib/useTelemetry";
import { AlertTriangle, BrainCircuit, FileText, Sparkles, Wifi, X } from "lucide-react";
import { Link, useNavigate } from "react-router-dom";
import { ModelManager } from "@/components/chat/ModelManager";
import { prefetchRoute } from "@/lib/prefetch";
import { useTranslation } from "@/lib/i18n";
import { useMaterialRipple } from "@/lib/ripple";
import { sendChat, FALLBACK_HEALTH_RECORDS } from "@/lib/apiChat";
import { API_BASE, authHeaders } from "@/lib/apiCore";
import { toast } from "@/lib/toast";
import { TelemetryAlarmSnoozeModal } from "@/components/modals/TelemetryAlarmSnoozeModal";
import { GuidedConsole } from "@/components/dashboard/GuidedConsole";
import { StatsGrid } from "@/components/dashboard/StatsGrid";
import { TelemetryGrid } from "@/components/dashboard/TelemetryGrid";
import { PatientProfileModal } from "@/components/dashboard/PatientProfileModal";
import { patientProfiles } from "@/components/dashboard/patientProfiles";
import { INITIAL_BEDS, type ClinicalBed } from "@/components/dashboard/mockBeds";
import { DiagnosticTrajectorySection } from "@/components/dashboard/DiagnosticTrajectorySection";
import { DepartmentLoadSection } from "@/components/dashboard/DepartmentLoadSection";
import { usePatientVitalsTelemetry } from "@/components/dashboard/usePatientVitalsTelemetry";
import { useWebLLMEngine } from "@/components/dashboard/useWebLLMEngine";

const RiskTrajectoryChart = lazy(() => import("@/components/operations/RiskTrajectoryChart"));
const OperationsCockpit = lazy(() => import("@/components/operations/OperationsCockpit"));
const LiveECGMonitor = lazy(() => import("@/components/operations/LiveECGMonitor"));

export default function DashboardPage() {
  const { user } = useAuthStore();
  const navigate = useNavigate();
  const { t } = useTranslation();
  const { triggerRipple } = useMaterialRipple();

  const [records, setRecords] = useState<HealthRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [demoReadiness, setDemoReadiness] = useState<any>(null);
  const [dbPatients, setDbPatients] = useState<any[]>([]);

  // Telemetry real-time polling hook
  const { data: telemetry, status: wsStatus } = useTelemetry();

  // Beds data and expanded view state
  const [beds, setBeds] = useState<ClinicalBed[]>(INITIAL_BEDS);
  const [expandedBed, setExpandedBed] = useState<string | null>(null);
  const [activeNurseCalls, setActiveNurseCalls] = useState<Record<string, boolean>>({});
  const [selectedBed, setSelectedBed] = useState<ClinicalBed | null>(null);
  const [codeBlueActive, setCodeBlueActive] = useState<Record<string, boolean>>({});

  // Active tab within the modal
  const [activeTab, setActiveTab] = useState<"insights" | "history" | "chat" | "vitals">("insights");

  // Chat copilot state within the modal
  const [chatMessages, setChatMessages] = useState<Array<{ role: string; content: string }>>([
    { role: "assistant", content: "Hello Doctor, I am analyzing this patient's live telemetry..." },
  ]);
  const [chatInput, setChatInput] = useState("");
  const [chatLoading, setChatLoading] = useState(false);

  // WebLLM Engine state hook
  const {
    showModelManager,
    setShowModelManager,
    selectedModel,
    setSelectedModel,
    currentWebLLMModel,
    setCurrentWebLLMModel,
    webllmActive,
    setWebllmActive,
    webllmLoading,
    webllmProgress,
    handleWebLLMLoad,
    handleWebLLMUnload,
  } = useWebLLMEngine();

  // Global telemetry alarm snooze state
  const [telemetryAlarmDismissed, setTelemetryAlarmDismissed] = useState(false);

  useEffect(() => {
    getRecords()
      .then(setRecords)
      .catch((err) => {
        console.warn("Records fetch fallback to demo records:", err);
        setRecords(FALLBACK_HEALTH_RECORDS);
      })
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    getDemoReadiness().then(setDemoReadiness).catch(console.error);
  }, []);

  useEffect(() => {
    if (user?.role === "admin" || user?.role === "doctor") {
      const fetchRegistry = user.role === "doctor" ? getDoctorPatients() : getAdminPatients();
      fetchRegistry
        .then(setDbPatients)
        .catch((err) => console.warn("Failed to pre-fetch patient registry: ", err));
    }
  }, [user]);

  const prevAlarmActiveRef = useRef<boolean | null>(null);
  useEffect(() => {
    const isAlertActive = !telemetryAlarmDismissed && beds[1].hr > 100;
    if (prevAlarmActiveRef.current !== isAlertActive) {
      prevAlarmActiveRef.current = isAlertActive;
      window.dispatchEvent(
        new CustomEvent("clinical-alarm", {
          detail: {
            active: isAlertActive,
            bed: "ICU-A-01",
            name: "Marcus Thorne",
            hr: beds[1].hr,
          },
        })
      );
    }
  }, [telemetryAlarmDismissed, beds]);

  const [snoozingAlarmBed, setSnoozingAlarmBed] = useState<{
    bedCode: string;
    patientName?: string;
    alarmTitle: string;
  } | null>(null);

  useEffect(() => {
    const handleResolve = (e: Event) => {
      const customEvt = e as CustomEvent;
      const action = customEvt.detail?.action;
      if (action === "dismiss") {
        setTelemetryAlarmDismissed(true);
        toast.info("Telemetry alarm sound muted for ICU Section A-1.");
      } else if (action === "snooze") {
        setSnoozingAlarmBed({
          bedCode: customEvt.detail?.bed || "ICU-A-01",
          patientName: customEvt.detail?.name || "Marcus Thorne",
          alarmTitle: "Sustained Tachycardia Alert",
        });
      }
    };
    window.addEventListener("resolve-alarm", handleResolve);
    return () => window.removeEventListener("resolve-alarm", handleResolve);
  }, []);

  const selectedPatientDbId = useMemo(() => {
    if (!selectedBed) return null;
    const matchingDbPatient = dbPatients.find(
      (p: any) =>
        p.full_name?.toLowerCase().includes(selectedBed.name.toLowerCase()) ||
        p.username?.toLowerCase().includes(selectedBed.name.toLowerCase()) ||
        selectedBed.name.toLowerCase().includes(p.full_name?.toLowerCase() || "") ||
        selectedBed.name.toLowerCase().includes(p.username?.toLowerCase() || "")
    );
    const staticIdMap: Record<string, number> = {
      "Sarah Jenkins": 2,
      "Marcus Thorne": 3,
      "Linda Zhao": 4,
      "Robert G.": 3,
      "Emily Watson": 4,
      "Oscar M.": 5,
    };
    return matchingDbPatient?.patient_id || matchingDbPatient?.id || staticIdMap[selectedBed.name] || 1;
  }, [selectedBed, dbPatients]);

  // Vitals & signals state management via custom hook
  const {
    vitalsHr,
    setVitalsHr,
    vitalsSpo2,
    setVitalsSpo2,
    vitalsSystolic,
    setVitalsSystolic,
    vitalsDiastolic,
    setVitalsDiastolic,
    vitalsRr,
    setVitalsRr,
    vitalsTemp,
    setVitalsTemp,
    vitalsGlucose,
    setVitalsGlucose,
    isSubmittingVitals,
    handleVitalsSubmit,
    activeSignals,
    signalsLoading,
  } = usePatientVitalsTelemetry({
    selectedPatientDbId,
    selectedBed,
    setSelectedBed,
    setBeds,
    activeTab,
  });

  useEffect(() => {
    if (!dbPatients || dbPatients.length === 0) return;
    setBeds((prevBeds) =>
      prevBeds.map((bed) => {
        const matchingPatient = dbPatients.find(
          (p) => p.full_name?.toLowerCase() === bed.name.toLowerCase()
        );
        if (!matchingPatient) return bed;
        return {
          ...bed,
          status:
            (matchingPatient as any).triage_acuity === "immediate" ||
            (matchingPatient as any).triage_acuity === "emergency"
              ? "Alert"
              : bed.status,
        };
      })
    );
  }, [dbPatients]);

  const highRiskRecords = records.filter((r) => {
    const pred = (r.prediction || "").toLowerCase();
    return pred.includes("high") || pred.includes("positive") || pred.includes("disease");
  });
  const recentRecords = records.slice(0, 5);

  const displayChartData = useMemo(() => {
    const chartData = records
      .slice(0, 10)
      .reverse()
      .map((r) => {
        const pred = (r.prediction || "").toLowerCase();
        const ts = r.timestamp || r.created_at || new Date().toISOString();
        return {
          name: new Date(ts).toLocaleDateString(undefined, { month: "short", day: "numeric" }),
          riskScore:
            pred.includes("high") || pred.includes("positive")
              ? 80
              : pred.includes("medium")
                ? 50
                : 20,
        };
      });
    return chartData.length > 0
      ? chartData
      : [
          { name: "Jan 1", riskScore: 10 },
          { name: "Jan 5", riskScore: 15 },
          { name: "Jan 12", riskScore: 12 },
          { name: "Jan 18", riskScore: 25 },
          { name: "Jan 25", riskScore: 20 },
          { name: "Today", riskScore: 15 },
        ];
  }, [records]);

  const patientDbIdMap = useMemo(() => {
    const map: Record<string, number> = {};
    const staticIdMap: Record<string, number> = {
      "Sarah Jenkins": 2,
      "Marcus Thorne": 3,
      "Linda Zhao": 4,
      "Robert G.": 3,
      "Emily Watson": 4,
      "Oscar M.": 5,
    };

    beds.forEach((bed) => {
      const matchingDbPatient = dbPatients.find(
        (p: any) =>
          p.full_name?.toLowerCase().includes(bed.name.toLowerCase()) ||
          p.username?.toLowerCase().includes(bed.name.toLowerCase()) ||
          bed.name.toLowerCase().includes(p.full_name?.toLowerCase() || "") ||
          bed.name.toLowerCase().includes(p.username?.toLowerCase() || "")
      );
      const patientDbId = matchingDbPatient?.patient_id || matchingDbPatient?.id;
      map[bed.name] = patientDbId || staticIdMap[bed.name] || 1;
    });

    return map;
  }, [beds, dbPatients]);

  const capacityPct =
    telemetry && telemetry.total_capacity && telemetry.total_capacity > 0
      ? Math.round(((telemetry.active_census ?? 0) / telemetry.total_capacity) * 100)
      : 79;

  const stableBedsCount = beds.filter((b) => b.status === "Stable").length;
  const alertBedsCount = beds.filter((b) => b.status === "Alert").length;

  return (
    <div className="w-full space-y-6 pb-12 selection:bg-[var(--accent)] selection:text-white relative">
      {/* System ribbon */}
      <div
        className="glass-card px-4 py-2 flex flex-col md:flex-row md:items-center md:justify-between gap-2 font-mono text-[10px] tracking-wider text-[var(--text-dim)] uppercase"
        role="status"
        aria-label="System status bar"
      >
        <div className="flex flex-wrap items-center gap-x-4 gap-y-1.5">
          {demoReadiness?.status === "demo-ready" && (
            <span className="flex items-center gap-1.5 text-[var(--accent)] font-semibold">
              <span
                className="w-1.5 h-1.5 rounded-full bg-[var(--accent)] animate-pulse"
                aria-hidden="true"
              />
              Demo Ready
            </span>
          )}
          <span className="flex items-center gap-1.5 text-[var(--success)] font-semibold">
            <span
              className="w-1.5 h-1.5 rounded-full bg-[var(--success)] animate-pulse"
              aria-hidden="true"
            />
            HL7 STREAM ACTIVE
          </span>
          <span>NODE: CARE-MED-09</span>
          <span>AUTH: JWT SESSION</span>
        </div>
        <div className="flex flex-wrap items-center gap-x-4 gap-y-1.5">
          <span>
            LATENCY: {telemetry?.system_latency_ms != null ? telemetry.system_latency_ms : "--"}ms
          </span>
          <span>UPTIME: 99.999%</span>
          {wsStatus === "connected" ? (
            <span className="flex items-center gap-1 text-[var(--success)] font-semibold">
              <Wifi size={11} aria-hidden="true" /> WS LIVE
            </span>
          ) : wsStatus === "connecting" ? (
            <span className="flex items-center gap-1 text-amber-400 font-semibold">
              <Wifi size={11} aria-hidden="true" className="animate-pulse" /> WS CONNECTING
            </span>
          ) : (
            <span className="flex items-center gap-1 text-emerald-400 font-semibold">
              <Wifi size={11} aria-hidden="true" /> TELEMETRY ACTIVE
            </span>
          )}
        </div>
      </div>

      {error && (
        <div
          className="flex items-center justify-between gap-2 p-3 text-xs font-mono uppercase tracking-wide border border-[var(--warning-border)] bg-[var(--warning-muted)] text-[var(--warning)] rounded"
          role="alert"
        >
          <div className="flex items-center gap-2">
            <AlertTriangle size={14} className="shrink-0" />
            <span>{error}</span>
          </div>
          <button
            onClick={() => setError(null)}
            className="p-1 hover:bg-black/20 rounded transition-colors text-[var(--text-secondary)] hover:text-white"
            aria-label="Dismiss warning"
          >
            <X size={14} />
          </button>
        </div>
      )}

      {/* Header */}
      <header className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-[var(--border)] pb-4">
        <div>
          <h1 className="text-xl font-bold text-[var(--text-primary)] uppercase tracking-wider font-display">
            Clinical Overview
          </h1>
          <p className="text-xs text-[var(--text-secondary)] font-mono uppercase tracking-wide flex items-center gap-1.5 mt-1">
            <BrainCircuit size={12} className="text-[var(--accent)]" />
            {t.welcome}: {user?.full_name || user?.username || "Dr. Admin"} (ICU Section A-1)
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Link to="/patients" onMouseEnter={() => prefetchRoute("/patients")}>
            <button
              onClick={triggerRipple}
              className="btn btn-secondary text-xs uppercase tracking-wider flex items-center gap-1.5"
              aria-label="Open EMR Database"
            >
              <FileText size={13} /> {t.patientRegistry}
            </button>
          </Link>
          <Link to="/chat" onMouseEnter={() => prefetchRoute("/chat")}>
            <button
              onClick={triggerRipple}
              className="btn btn-primary text-xs uppercase tracking-wider flex items-center gap-1.5"
              aria-label="Engage AI Copilot"
            >
              <Sparkles size={13} /> {t.engageCopilot}
            </button>
          </Link>
        </div>
      </header>

      {/* Zero Learning Curve Guided Console & Quick Actions */}
      <GuidedConsole
        navigate={navigate}
        triggerRipple={triggerRipple}
        toast={toast}
        apiBase={API_BASE}
        authHeaders={authHeaders}
      />

      {/* Aggregated Stats Grid */}
      <StatsGrid
        telemetry={telemetry}
        capacityPct={capacityPct}
        alertBedsCount={alertBedsCount}
        stableBedsCount={stableBedsCount}
        recordsCount={records.length}
        highRiskCount={highRiskRecords.length}
      />

      {/* Level 1: Clinical Telemetry Grid */}
      <TelemetryGrid
        beds={beds}
        expandedBed={expandedBed}
        setExpandedBed={setExpandedBed}
        patientDbIdMap={patientDbIdMap}
        navigate={navigate}
        LiveECGMonitor={LiveECGMonitor}
        activeNurseCalls={activeNurseCalls}
        setActiveNurseCalls={setActiveNurseCalls}
        setSelectedBed={setSelectedBed}
        setActiveTab={setActiveTab}
        setChatMessages={setChatMessages}
      />

      {/* Level 2: Recharts Population Risk Trajectory Chart & Live Diagnostic Stream */}
      <DiagnosticTrajectorySection
        telemetry={telemetry}
        triggerRipple={triggerRipple}
        displayChartData={displayChartData}
        RiskTrajectoryChart={RiskTrajectoryChart}
        recentRecords={recentRecords}
        loading={loading}
      />

      <OperationsCockpit />

      {/* Level 3: Department Load & Resources */}
      <DepartmentLoadSection departmentLoads={telemetry?.department_loads} />

      {/* Patient Profile & Clinical Assessment Modal */}
      <PatientProfileModal
        selectedBed={selectedBed}
        onClose={() => setSelectedBed(null)}
        patientProfiles={patientProfiles}
        codeBlueActive={codeBlueActive}
        setCodeBlueActive={setCodeBlueActive}
        dbPatients={dbPatients}
        navigate={navigate}
        apiBase={API_BASE}
        authHeaders={authHeaders}
        toast={toast}
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        chatMessages={chatMessages}
        setChatMessages={setChatMessages}
        chatLoading={chatLoading}
        setChatLoading={setChatLoading}
        chatInput={chatInput}
        setChatInput={setChatInput}
        webllmActive={webllmActive}
        webllmProgress={webllmProgress}
        selectedModel={selectedModel}
        setShowModelManager={setShowModelManager}
        selectedPatientDbId={selectedPatientDbId}
        vitalsHr={vitalsHr}
        setVitalsHr={setVitalsHr}
        vitalsSpo2={vitalsSpo2}
        setVitalsSpo2={setVitalsSpo2}
        vitalsSystolic={vitalsSystolic}
        setVitalsSystolic={setVitalsSystolic}
        vitalsDiastolic={vitalsDiastolic}
        setVitalsDiastolic={setVitalsDiastolic}
        vitalsRr={vitalsRr}
        setVitalsRr={setVitalsRr}
        vitalsTemp={vitalsTemp}
        setVitalsTemp={setVitalsTemp}
        vitalsGlucose={vitalsGlucose}
        setVitalsGlucose={setVitalsGlucose}
        isSubmittingVitals={isSubmittingVitals}
        handleVitalsSubmit={handleVitalsSubmit}
        signalsLoading={signalsLoading}
        activeSignals={activeSignals}
        sendChat={sendChat}
      />

      {showModelManager && (
        <ModelManager
          onClose={() => setShowModelManager(false)}
          onOllamaSelect={(m) => {
            setSelectedModel(m);
            setWebllmActive(false);
          }}
          onWebLLMSelect={(m) => {
            setCurrentWebLLMModel(m);
          }}
          onWebLLMUnload={handleWebLLMUnload}
          onWebLLMLoad={handleWebLLMLoad}
          currentOllamaModel={selectedModel}
          currentWebLLMModel={currentWebLLMModel}
          webllmActive={webllmActive}
          webllmLoading={webllmLoading}
          webllmProgress={webllmProgress}
        />
      )}

      {snoozingAlarmBed && (
        <TelemetryAlarmSnoozeModal
          bedCode={snoozingAlarmBed.bedCode}
          patientName={snoozingAlarmBed.patientName}
          alarmTitle={snoozingAlarmBed.alarmTitle}
          onClose={() => setSnoozingAlarmBed(null)}
          onSnoozeComplete={() => setSnoozingAlarmBed(null)}
        />
      )}
    </div>
  );
}
