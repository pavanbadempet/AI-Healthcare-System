import { useEffect, useState, useMemo, lazy, Suspense } from "react";
import { useAuthStore } from "@/lib/auth";
import { getRecords, getDemoReadiness, type HealthRecord } from "@/lib/api";
import { useTelemetry } from "@/lib/useTelemetry";
import { motion, AnimatePresence } from "framer-motion";
import { 
  Activity, Clock, FileText, AlertTriangle, Sparkles, BrainCircuit, 
  Wifi, WifiOff, Heart, Thermometer, ShieldAlert, ArrowRight, 
  TrendingUp, BellRing, UserCheck, RefreshCw 
} from "lucide-react";
import { Link } from "react-router-dom";

const RiskTrajectoryChart = lazy(() => import("@/components/operations/RiskTrajectoryChart"));
import OperationsCockpit from "@/components/operations/OperationsCockpit";
import { prefetchRoute } from "@/lib/prefetch";
import { useTranslation } from "@/lib/i18n";

interface ClinicalBed {
  bed: string;
  name: string;
  status: "Stable" | "Alert";
  hr: number;
  spo2: number;
  bp: string;
  rr: number;
  ecgD: string;
}

export default function DashboardPage() {
  const { user } = useAuthStore();
  const { t } = useTranslation();
  const [records, setRecords] = useState<HealthRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const { data: telemetry, status: wsStatus } = useTelemetry();
  const [demoReadiness, setDemoReadiness] = useState<{ status: string } | null>(null);
  const [error, setError] = useState("");
  const [expandedBed, setExpandedBed] = useState<string | null>(null);

  // Live telemetry beds state
  const [beds, setBeds] = useState<ClinicalBed[]>([
    {
      bed: "Bed 12A",
      name: "Sarah Jenkins",
      status: "Stable",
      hr: 72,
      spo2: 98,
      bp: "120/80",
      rr: 16,
      ecgD: "M0,50 L50,50 L60,20 L70,80 L80,50 L120,50 L130,20 L140,80 L150,50 L200,50 L210,10 L220,90 L230,50 L280,50 L290,20 L300,80 L310,50 L360,50 L370,20 L380,80 L390,50 L400,50"
    },
    {
      bed: "Bed 14C",
      name: "Marcus Thorne",
      status: "Alert",
      hr: 118,
      spo2: 94,
      bp: "145/95",
      rr: 24,
      ecgD: "M0,50 L30,50 L35,10 L45,90 L55,50 L80,50 L85,10 L95,90 L105,50 L130,50 L135,10 L145,90 L155,50 L180,50 L185,10 L195,90 L205,50 L230,50 L235,10 L245,90 L255,50 L280,50 L285,10 L295,90 L305,50 L330,50 L335,10 L345,90 L355,50 L380,50 L385,10 L395,90 L400,50"
    },
    {
      bed: "Bed 08B",
      name: "Linda Zhao",
      status: "Stable",
      hr: 64,
      spo2: 99,
      bp: "115/75",
      rr: 14,
      ecgD: "M0,50 L40,50 L50,15 L60,85 L70,50 L110,50 L120,15 L130,85 L140,50 L180,50 L190,15 L200,85 L210,50 L250,50 L260,15 L270,85 L280,50 L320,50 L330,15 L340,85 L350,50 L400,50"
    },
    {
      bed: "Bed 10D",
      name: "Robert G.",
      status: "Stable",
      hr: 85,
      spo2: 97,
      bp: "132/84",
      rr: 18,
      ecgD: "M0,50 L60,50 L70,25 L80,75 L90,50 L150,50 L160,25 L170,75 L180,50 L240,50 L250,25 L260,75 L270,50 L330,50 L340,25 L350,75 L360,50 L400,50"
    },
    {
      bed: "Bed 05A",
      name: "Emily Watson",
      status: "Stable",
      hr: 68,
      spo2: 98,
      bp: "112/68",
      rr: 15,
      ecgD: "M0,50 L55,50 L65,30 L75,70 L85,50 L140,50 L150,30 L160,70 L170,50 L225,50 L235,30 L245,70 L255,50 L310,50 L320,30 L330,70 L340,50 L400,50"
    },
    {
      bed: "Bed 11F",
      name: "Oscar Meyer",
      status: "Stable",
      hr: 76,
      spo2: 96,
      bp: "128/82",
      rr: 17,
      ecgD: "M0,50 L45,50 L55,20 L65,80 L75,50 L120,50 L130,20 L140,80 L150,50 L195,50 L205,20 L215,80 L225,50 L270,50 L280,20 L290,80 L300,50 L345,50 L355,20 L365,80 L375,50 L400,50"
    }
  ]);

  useEffect(() => {
    getRecords()
      .then(setRecords)
      .catch((err) => {
        console.error(err);
        setError("Backend connection unavailable. Demo data may be incomplete.");
      })
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    getDemoReadiness()
      .then(setDemoReadiness)
      .catch(console.error);
  }, []);



  // Simulating real-time updates for patient vitals
  useEffect(() => {
    const interval = setInterval(() => {
      setBeds((prevBeds) =>
        prevBeds.map((bed) => {
          // Stable beds fluctuate slightly, Alert bed (Marcus Thorne) fluctuates at higher rates
          const hrDelta = bed.status === "Alert" 
            ? Math.floor(Math.random() * 5) - 2 // -2 to 2
            : Math.floor(Math.random() * 3) - 1; // -1 to 1

          const newHr = Math.max(bed.status === "Alert" ? 110 : 55, Math.min(bed.status === "Alert" ? 130 : 95, bed.hr + hrDelta));
          const spo2Delta = Math.random() > 0.8 ? (Math.random() > 0.5 ? 1 : -1) : 0;
          const newSpo2 = Math.max(bed.status === "Alert" ? 90 : 95, Math.min(100, bed.spo2 + spo2Delta));
          const rrDelta = Math.random() > 0.7 ? (Math.random() > 0.5 ? 1 : -1) : 0;
          const newRr = Math.max(bed.status === "Alert" ? 20 : 12, Math.min(bed.status === "Alert" ? 28 : 20, bed.rr + rrDelta));

          return {
            ...bed,
            hr: newHr,
            spo2: newSpo2,
            rr: newRr
          };
        })
      );
    }, 2000);
    return () => clearInterval(interval);
  }, []);

  const highRiskRecords = records.filter(r =>
    r.prediction.toLowerCase().includes("high") ||
    r.prediction.toLowerCase().includes("positive") ||
    r.prediction.toLowerCase().includes("disease")
  );
  const recentRecords = records.slice(0, 5);

  const displayChartData = useMemo(() => {
    const chartData = records.slice(0, 10).reverse().map((r) => ({
      name: new Date(r.timestamp).toLocaleDateString(undefined, { month: "short", day: "numeric" }),
      riskScore: r.prediction.toLowerCase().includes("high") || r.prediction.toLowerCase().includes("positive") ? 80 : r.prediction.toLowerCase().includes("medium") ? 50 : 20,
    }));
    return chartData.length > 0
      ? chartData
      : [
          { name: "Jan 1", riskScore: 10 }, { name: "Jan 5", riskScore: 15 },
          { name: "Jan 12", riskScore: 12 }, { name: "Jan 18", riskScore: 25 },
          { name: "Jan 25", riskScore: 20 }, { name: "Today", riskScore: 15 },
        ];
  }, [records]);

  const capacityPct = telemetry
    ? Math.round((telemetry.active_census / telemetry.total_capacity) * 100)
    : 84;

  const stableBedsCount = beds.filter(b => b.status === "Stable").length;
  const alertBedsCount = beds.filter(b => b.status === "Alert").length;

  return (
    <div className="w-full space-y-6 pb-12 selection:bg-[var(--accent)] selection:text-white relative">
      
      {/* CSS Styles injection for ECG animations & status pulses */}
      <style>{`
        .ecg-line-animate {
          stroke-dasharray: 1000;
          stroke-dashoffset: 1000;
          animation: ecg-dash 5s linear infinite;
        }
        @keyframes ecg-dash {
          to {
            stroke-dashoffset: 0;
          }
        }
        .status-pulse-emerald {
          animation: pulse-emerald 2s infinite;
        }
        @keyframes pulse-emerald {
          0% { box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.4); }
          70% { box-shadow: 0 0 0 8px rgba(16, 185, 129, 0); }
          100% { box-shadow: 0 0 0 0 rgba(16, 185, 129, 0); }
        }
        .status-pulse-ruby {
          animation: pulse-ruby 1.5s infinite;
        }
        @keyframes pulse-ruby {
          0% { box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.4); }
          70% { box-shadow: 0 0 0 8px rgba(239, 68, 68, 0); }
          100% { box-shadow: 0 0 0 0 rgba(239, 68, 68, 0); }
        }
      `}</style>

      {/* System ribbon */}
      <div className="glass-card px-4 py-2 flex flex-col md:flex-row md:items-center md:justify-between gap-2 font-mono text-[10px] tracking-wider text-[var(--text-dim)] uppercase" role="status" aria-label="System status bar">
        <div className="flex flex-wrap items-center gap-x-4 gap-y-1.5">
          {demoReadiness?.status === "demo-ready" && (
            <span className="flex items-center gap-1.5 text-[var(--accent)] font-semibold">
              <span className="w-1.5 h-1.5 rounded-full bg-[var(--accent)] animate-pulse" aria-hidden="true" />
              Demo Ready
            </span>
          )}
          <span className="flex items-center gap-1.5 text-[var(--success)] font-semibold">
            <span className="w-1.5 h-1.5 rounded-full bg-[var(--success)] animate-pulse" aria-hidden="true" />
            HL7 STREAM ACTIVE
          </span>
          <span>NODE: CARE-MED-09</span>
          <span>AUTH: JWT SESSION</span>
        </div>
        <div className="flex flex-wrap items-center gap-x-4 gap-y-1.5">
          <span>LATENCY: {telemetry ? telemetry.system_latency_ms : "--"}ms</span>
          <span>UPTIME: 99.999%</span>
          {wsStatus === "connected" ? (
            <span className="flex items-center gap-1 text-[var(--success)] font-semibold"><Wifi size={11} aria-hidden="true" /> WS LIVE</span>
          ) : (
            <span className="flex items-center gap-1 text-[var(--danger)] font-semibold"><WifiOff size={11} aria-hidden="true" /> WS ERROR</span>
          )}
        </div>
      </div>

      {error && (
        <div className="flex items-center gap-2 p-3 text-xs font-mono uppercase tracking-wide border border-[var(--warning-border)] bg-[var(--warning-muted)] text-[var(--warning)] rounded animate-pulse" role="alert">
          <AlertTriangle size={14} className="shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Header */}
      <header className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-[var(--border)] pb-4">
        <div>
          <h1 className="text-xl font-bold text-[var(--text-primary)] uppercase tracking-wider font-display">
            Nexus Vitalis
          </h1>
          <p className="text-xs text-[var(--text-secondary)] font-mono uppercase tracking-wide flex items-center gap-1.5 mt-1">
            <BrainCircuit size={12} className="text-[var(--accent)]" />
            {t.welcome}: {user?.full_name || user?.username || "Dr. Admin"} (ICU Section A-1)
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Link to="/patients" onMouseEnter={() => prefetchRoute('/patients')}>
            <button className="btn btn-secondary text-xs uppercase tracking-wider flex items-center gap-1.5" aria-label="Open EMR Database">
              <FileText size={13} /> {t.patientRegistry}
            </button>
          </Link>
          <Link to="/chat" onMouseEnter={() => prefetchRoute('/chat')}>
            <button className="btn btn-primary text-xs uppercase tracking-wider flex items-center gap-1.5" aria-label="Engage AI Copilot">
              <Sparkles size={13} /> {t.engageCopilot}
            </button>
          </Link>
        </div>
      </header>

      {/* Aggregated Stats Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Card 1: ICU Active Census */}
        <div className="glass-card p-4 rounded-xl flex items-center justify-between group">
          <div className="space-y-1">
            <span className="text-[10px] font-bold uppercase tracking-wider text-[var(--text-secondary)]">Occupied Beds (ICU)</span>
            <div className="flex items-baseline gap-1">
              <span className="text-2xl font-black text-[var(--text-primary)] font-display">
                {telemetry ? telemetry.active_census : "12"}
              </span>
              <span className="text-[10px] text-[var(--text-dim)] font-mono">
                / {telemetry ? telemetry.total_capacity : "15"} Beds
              </span>
            </div>
            <p className="text-[9px] text-[var(--text-dim)] font-mono uppercase tracking-wide">
              {capacityPct}% Rooms In Use
            </p>
          </div>
          <div className="relative w-12 h-12 shrink-0">
            <svg className="w-full h-full transform -rotate-90" viewBox="0 0 36 36">
              <path
                className="text-white/[0.04]"
                strokeWidth="3"
                stroke="currentColor"
                fill="transparent"
                d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
              />
              <path
                className="text-[var(--accent)] transition-all duration-1000 ease-out"
                strokeWidth="3"
                strokeDasharray={`${capacityPct}, 100`}
                strokeLinecap="round"
                stroke="currentColor"
                fill="transparent"
                d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
              />
            </svg>
            <div className="absolute inset-0 flex items-center justify-center text-[10px] font-mono font-bold text-[var(--text-secondary)]">
              {capacityPct}%
            </div>
          </div>
        </div>

        {/* Card 2: Alerts Active */}
        <div className="glass-card p-4 rounded-xl flex items-center justify-between group">
          <div className="space-y-1">
            <span className="text-[10px] font-bold uppercase tracking-wider text-[var(--text-secondary)]">Active Alarms</span>
            <div className="flex items-baseline gap-1">
              <span className={`text-2xl font-black font-display ${alertBedsCount > 0 ? "text-[var(--danger)] animate-pulse" : "text-[var(--text-primary)]"}`}>
                {alertBedsCount}
              </span>
              <span className="text-[10px] text-[var(--text-dim)] font-mono">Alerts</span>
            </div>
            <p className="text-[9px] text-[var(--text-dim)] font-mono uppercase tracking-wide">
              {stableBedsCount} Stable Patients
            </p>
          </div>
          <div className={`w-10 h-10 rounded-full flex items-center justify-center border shrink-0 ${
            alertBedsCount > 0 
              ? "bg-[var(--danger-muted)] border-[var(--danger-border)] status-pulse-ruby" 
              : "bg-white/[0.02] border-white/[0.04]"
          }`}>
            <AlertTriangle size={18} className={alertBedsCount > 0 ? "text-[var(--danger)] animate-bounce" : "text-[var(--text-dim)]"} />
          </div>
        </div>

        {/* Card 3: Network Latency */}
        <div className="glass-card p-4 rounded-xl flex items-center justify-between group">
          <div className="space-y-1">
            <span className="text-[10px] font-bold uppercase tracking-wider text-[var(--text-secondary)]">
              {telemetry?.spark_batch_id !== undefined ? "Spark Engine Latency" : "Server Connection"}
            </span>
            <div className="flex items-baseline gap-1">
              <span className="text-2xl font-black text-[var(--text-primary)] font-display">
                {telemetry ? telemetry.system_latency_ms : "14"}
              </span>
              <span className="text-[10px] text-[var(--text-dim)] font-mono">ms Speed</span>
            </div>
            <p className="text-[9px] text-[var(--text-dim)] font-mono uppercase tracking-wide flex items-center gap-1">
              <span className="w-1.5 h-1.5 rounded-full bg-[var(--success)] animate-pulse" />
              {telemetry?.spark_batch_id !== undefined ? `Batch #${telemetry.spark_batch_id} Ingest` : "Normal Sync"}
            </p>
          </div>
          <div className="w-10 h-10 rounded-full flex items-center justify-center border border-white/[0.04] bg-white/[0.02] shrink-0">
            <Activity size={18} className="text-[var(--accent-blue)] animate-pulse" />
          </div>
        </div>

        {/* Card 4: AI Risk Assessments */}
        <div className="glass-card p-4 rounded-xl flex items-center justify-between group">
          <div className="space-y-1">
            <span className="text-[10px] font-bold uppercase tracking-wider text-[var(--text-secondary)]">AI Diagnosis Checks</span>
            <div className="flex items-baseline gap-1">
              <span className="text-2xl font-black text-[var(--text-primary)] font-display">
                {records.length}
              </span>
              <span className="text-[10px] text-[var(--text-dim)] font-mono">Checked</span>
            </div>
            <p className="text-[9px] text-[var(--text-dim)] font-mono uppercase tracking-wide">
              {highRiskRecords.length} High Risks Found
            </p>
          </div>
          <div className="w-10 h-10 rounded-full flex items-center justify-center border border-[var(--accent-purple-border)] bg-[var(--accent-purple-muted)] shrink-0">
            <Sparkles size={16} className="text-[var(--accent-purple)]" />
          </div>
        </div>
      </div>

      {/* Triage Overview & Telemetry status */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-white/[0.01] border border-white/[0.04] p-4 rounded-2xl">
        <div>
          <h2 className="text-sm font-bold text-[var(--text-primary)] uppercase tracking-wider">Live Patient Telemetry</h2>
          <p className="text-xs text-[var(--text-secondary)] mt-0.5">Monitoring {beds.length} Active Clinical Beds</p>
        </div>

        {telemetry?.spark_batch_id !== undefined && (
          <motion.div 
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="flex flex-wrap items-center gap-x-4 gap-y-1.5 bg-black/40 px-4 py-2 rounded-xl border border-white/[0.04] text-[10px] font-mono text-[var(--text-secondary)] uppercase tracking-wide"
          >
            <span className="flex items-center gap-1.5 text-[var(--accent-blue)] font-bold">
              <span className="w-1.5 h-1.5 rounded-full bg-[var(--accent-blue)] animate-ping" />
              Spark Stream Engine
            </span>
            <span className="border-l border-white/10 pl-3">Batch #{telemetry.spark_batch_id}</span>
            <span className="border-l border-white/10 pl-3">In-Memory Ingest: {telemetry.spark_records_processed ?? 0} Recs</span>
            <span className="border-l border-white/10 pl-3">Process Time: {telemetry.system_latency_ms} ms</span>
            {telemetry.spark_ml_latency_ms !== undefined && (
              <span className="border-l border-white/10 pl-3">ML Inference: {telemetry.spark_ml_latency_ms.toFixed(1)} ms</span>
            )}
          </motion.div>
        )}

        <div className="flex flex-wrap gap-2">
          <span className="flex items-center gap-2 bg-[var(--success-muted)] text-[var(--success)] px-3 py-1.5 rounded-full border border-[var(--success-border)] text-xs font-bold uppercase tracking-wider">
            <span className="w-1.5 h-1.5 rounded-full bg-[var(--success)] status-pulse-emerald"></span>
            {stableBedsCount} Stable
          </span>
          <span className="flex items-center gap-2 bg-[var(--danger-muted)] text-[var(--danger)] px-3 py-1.5 rounded-full border border-[var(--danger-border)] text-xs font-bold uppercase tracking-wider">
            <span className="w-1.5 h-1.5 rounded-full bg-[var(--danger)] status-pulse-ruby"></span>
            {alertBedsCount} Review Required
          </span>
        </div>
      </div>

      {/* Level 1: Nexus Vitalis Clinical Telemetry Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6" role="region" aria-label="Clinical Vital Monitors">
        {beds.map((bed, idx) => {
          const isAlert = bed.status === "Alert";
          const isExpanded = expandedBed === bed.bed;
          return (
            <motion.div
              key={bed.bed}
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: idx * 0.05 }}
              onClick={() => setExpandedBed(isExpanded ? null : bed.bed)}
              className={`glass-card rounded-2xl p-5 relative overflow-hidden group transition-colors duration-300 cursor-pointer h-fit ${
                isAlert 
                  ? "ring-1 ring-[var(--danger)]/30 bg-[var(--danger-muted)]/40 hover:bg-[var(--danger-muted)]/60" 
                  : isExpanded 
                    ? "border-[var(--accent)] bg-white/[0.03] shadow-glow-indigo"
                    : "hover:border-[var(--accent)]/30"
              }`}
            >
              {/* Header: Bed and Status */}
              <div className="flex justify-between items-start mb-4">
                <div>
                  <span className={`font-bold text-xs tracking-widest uppercase ${isAlert ? "text-[var(--danger)]" : "text-[var(--accent)]"}`}>
                    {bed.bed}
                  </span>
                  <h4 className="text-base font-bold text-[var(--text-primary)] uppercase tracking-wide mt-0.5">
                    {bed.name}
                  </h4>
                </div>
                <div className={`flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[10px] font-bold uppercase ${
                  isAlert 
                    ? "bg-[var(--danger-muted)] text-[var(--danger)] border border-[var(--danger-border)] status-pulse-ruby" 
                    : "bg-[var(--success-muted)] text-[var(--success)] border border-[var(--success-border)]"
                }`}>
                  <span className={`w-1.5 h-1.5 rounded-full ${isAlert ? "bg-[var(--danger)] animate-ping" : "bg-[var(--success)]"}`} />
                  {bed.status}
                </div>
              </div>

              {/* Animated ECG Waveform */}
              <div className="h-20 w-full mb-5 relative bg-black/20 rounded-lg p-1 border border-white/[0.02]">
                  <svg viewBox="0 0 400 100" className="w-full h-full overflow-visible">
                    <path
                      className={`ecg-line-animate fill-none ${isAlert ? "stroke-[var(--danger)]" : "stroke-[var(--accent-blue)]"}`}
                      d={bed.ecgD}
                      strokeWidth={2.5}
                      style={{
                        animationDuration: isAlert ? "3s" : "5s",
                        filter: isAlert ? "drop-shadow(0 0 4px var(--danger))" : "drop-shadow(0 0 4px var(--accent-blue))"
                      }}
                    />
                  </svg>
                <div className="absolute inset-0 bg-gradient-to-r from-transparent via-transparent to-[var(--bg-card)]/40 pointer-events-none" />
              </div>

              {/* Vitals Readings Grid */}
              <div className="grid grid-cols-2 gap-3">
                
                {/* Heart Rate */}
                <div className={`rounded-xl p-2.5 border flex flex-col justify-between ${
                  isAlert 
                    ? "bg-[var(--danger-muted)]/50 border-[var(--danger-border)]" 
                    : "bg-white/[0.02] border-white/[0.04] group-hover:border-white/[0.08]"
                }`}>
                  <span className={`text-[9px] font-bold uppercase tracking-wider ${isAlert ? "text-[var(--danger)]" : "text-[var(--text-secondary)]"}`}>
                    Heart Rate
                  </span>
                  <div className="flex items-baseline gap-1 mt-1">
                    <Heart size={12} className={`shrink-0 self-center ${isAlert ? "text-[var(--danger)] animate-bounce" : "text-[var(--accent)]"}`} />
                    <span className={`font-mono text-2xl font-black ${isAlert ? "text-[var(--danger)]" : "text-[var(--text-primary)]"}`}>
                      {bed.hr}
                    </span>
                    <span className="text-[10px] text-[var(--text-dim)] uppercase">BPM</span>
                  </div>
                </div>

                {/* SpO2 */}
                <div className="bg-white/[0.02] border border-white/[0.04] group-hover:border-white/[0.08] rounded-xl p-2.5 flex flex-col justify-between">
                  <span className="text-[9px] text-[var(--text-secondary)] font-bold uppercase tracking-wider">SpO2</span>
                  <div className="flex items-baseline gap-1 mt-1">
                    <Activity size={12} className="text-[var(--success)] shrink-0 self-center" />
                    <span className="font-mono text-2xl font-black text-[var(--success)]">
                      {bed.spo2}
                    </span>
                    <span className="text-[10px] text-[var(--text-dim)] uppercase">%</span>
                  </div>
                </div>

                {/* Blood Pressure */}
                <div className="bg-white/[0.02] border border-white/[0.04] group-hover:border-white/[0.08] rounded-xl p-2.5 flex flex-col justify-between">
                  <span className="text-[9px] text-[var(--text-secondary)] font-bold uppercase tracking-wider">Blood Pressure</span>
                  <div className="flex items-baseline gap-1 mt-1">
                    <span className="font-mono text-lg font-black text-[var(--text-primary)]">
                      {bed.bp}
                    </span>
                    <span className="text-[10px] text-[var(--text-dim)] uppercase">mmHg</span>
                  </div>
                </div>

                {/* Respiration */}
                <div className="bg-white/[0.02] border border-white/[0.04] group-hover:border-white/[0.08] rounded-xl p-2.5 flex flex-col justify-between">
                  <span className="text-[9px] text-[var(--text-secondary)] font-bold uppercase tracking-wider">Respiration</span>
                  <div className="flex items-baseline gap-1 mt-1">
                    <span className="font-mono text-lg font-black text-[var(--text-primary)]">
                      {bed.rr}
                    </span>
                    <span className="text-[10px] text-[var(--text-dim)] uppercase">RPM</span>
                  </div>
                </div>

              </div>

              {/* Expandable Details Area */}
              <AnimatePresence initial={false}>
                {isExpanded && (
                  <motion.div
                    initial={{ height: 0, opacity: 0 }}
                    animate={{ height: "auto", opacity: 1 }}
                    exit={{ height: 0, opacity: 0 }}
                    transition={{ duration: 0.25, ease: "easeInOut" }}
                    className="overflow-hidden mt-4 pt-4 border-t border-white/[0.04] space-y-3 text-xs"
                  >
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <span className="text-[10px] text-[var(--text-dim)] uppercase font-mono block">Patient EHR Status</span>
                        <p className="text-[var(--text-secondary)] mt-0.5">Admitted: 48 hours ago</p>
                        <p className="text-[var(--text-secondary)]">Condition: {isAlert ? "Decompensating" : "Stable / Recovery"}</p>
                      </div>
                      <div>
                        <span className="text-[10px] text-[var(--text-dim)] uppercase font-mono block">Clinical Diagnostics</span>
                        <div className="flex items-center gap-1.5 mt-0.5 text-[var(--text-secondary)]">
                          <Thermometer size={12} className="text-[var(--accent-purple)]" />
                          <span>Temp: {isAlert ? "101.4 °F" : "98.6 °F"}</span>
                        </div>
                        <div className="flex items-center gap-1.5 text-[var(--text-secondary)]">
                          <Clock size={12} className="text-[var(--accent-blue)]" />
                          <span>Last Scan: 14 mins ago</span>
                        </div>
                      </div>
                    </div>

                    <div className="bg-white/[0.01] border border-white/[0.03] p-2.5 rounded-lg font-mono text-[10px] text-[var(--text-dim)] space-y-1">
                      <div className="flex justify-between">
                        <span>HL7 MESSAGE:</span>
                        <span className="text-[var(--text-secondary)]">ADT^A08 EVENT</span>
                      </div>
                      <div className="flex justify-between">
                        <span>ALARM CODE:</span>
                        <span className={isAlert ? "text-[var(--danger)] font-bold animate-pulse" : "text-[var(--success)]"}>
                          {isAlert ? "SYS_ALARM_TACHY" : "SYS_NORMAL"}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span>TELEMETRY CHANNEL:</span>
                        <span className="text-[var(--text-secondary)]">CH_ECG_II_PRIMARY</span>
                      </div>
                    </div>

                    <div className="flex gap-2">
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          alert(`Initiated AI Clinical Assessment for ${bed.name}`);
                        }}
                        className="btn btn-secondary flex-1 py-1 text-[10px] font-bold uppercase tracking-wider border-white/[0.06] hover:border-[var(--accent-blue)]/50"
                      >
                        🔬 Run AI Check
                      </button>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          alert(`Contacting charge nurse for ${bed.bed}`);
                        }}
                        className="btn btn-primary flex-1 py-1 text-[10px] font-bold uppercase tracking-wider bg-[var(--accent)] hover:bg-[var(--accent-hover)]"
                      >
                        📞 Call Nurse
                      </button>
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </motion.div>
          );
        })}
      </div>

      {/* Right side alert box floating for Tachycardia */}
      <div className="fixed bottom-6 right-6 z-40 max-w-sm pointer-events-auto">
        <AnimatePresence>
          <motion.div
            initial={{ opacity: 0, scale: 0.9, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            className="panel p-4 rounded-xl border-l-4 border-[var(--danger)] shadow-[0_20px_40px_rgba(0,0,0,0.7)] bg-[var(--bg-card)]/90 backdrop-blur-2xl flex items-start gap-3 relative"
          >
            <BellRing className="text-[var(--danger)] shrink-0 mt-0.5 animate-pulse" size={16} />
            <div className="flex-1">
              <p className="font-bold text-xs text-[var(--text-primary)] uppercase tracking-wide">🚨 EMERGENCY ALARM: Very High Heart Rate!</p>
              <p className="text-[11px] text-[var(--text-secondary)] mt-1 font-mono">
                Bed 14C: Marcus Thorne is exhibiting abnormal heart rates (HR: {beds[1].hr} BPM).
              </p>
              <div className="flex flex-col gap-2 mt-3">
                <button 
                  onClick={() => alert("Dispatching Code Blue response team to Bed 14C.")}
                  className="btn btn-danger text-[10px] py-1.5 px-3 uppercase tracking-wider font-bold w-full"
                >
                  🚨 Send Emergency Team (Code Blue)
                </button>
                <button 
                  onClick={() => alert("Awaiting physician confirmation.")}
                  className="btn btn-secondary text-[10px] py-1.5 px-3 uppercase tracking-wider font-bold w-full"
                >
                  ❌ Stop Alarm / Dismiss
                </button>
              </div>
            </div>
          </motion.div>
        </AnimatePresence>
      </div>

      {/* Level 2: Recharts Population Risk Trajectory Chart & Live Diagnostic Stream */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Risk Trajectory Chart */}
        <div className="lg:col-span-2 panel flex flex-col overflow-hidden">
          <div className="panel-header flex justify-between items-center bg-[rgba(15,15,17,0.5)]">
            <div>
              <h2 className="section-title">Population Risk Trajectory</h2>
              <p className="mono-meta mt-0.5">
                AGGREGATED PREDICTIVE MODELING (N={telemetry ? telemetry.active_census.toLocaleString() : "1,248"})
              </p>
            </div>
            <div className="flex gap-1" role="group" aria-label="Time range selector">
              {["7D", "30D", "90D"].map((range) => (
                <button
                  key={range}
                  className={`px-2 py-0.5 border text-[9px] font-bold tracking-wider rounded transition-colors ${
                    range === "30D"
                      ? "bg-[var(--accent-muted)] border-[var(--accent-border)] text-[var(--accent)]"
                      : "bg-[var(--bg-card)] border-[var(--border)] text-[var(--text-dim)] hover:text-[var(--text-primary)]"
                  }`}
                  aria-label={`${range} view`}
                >
                  {range}
                </button>
              ))}
            </div>
          </div>
          
          <div className="p-4 flex-1">
            <div className="h-64 w-full overflow-hidden flex items-center justify-center">
              <Suspense fallback={
                <div className="flex flex-col items-center gap-3">
                  <div className="w-6 h-6 border-2 border-[var(--accent)] border-t-transparent rounded-full animate-spin" />
                  <p className="text-[10px] text-[var(--text-dim)] uppercase tracking-wider font-mono">Initializing Telemetry Engine...</p>
                </div>
              }>
                <RiskTrajectoryChart data={displayChartData} />
              </Suspense>
            </div>
          </div>
        </div>

        {/* Live Diagnostic Stream */}
        <div className="panel flex flex-col overflow-hidden">
          <div className="panel-header flex justify-between items-center bg-[rgba(15,15,17,0.5)]">
            <h2 className="section-title flex items-center gap-2">
              <Activity size={12} className="text-[var(--success)]" aria-hidden="true" /> Diagnostic Stream
            </h2>
            <span className="text-[9px] font-mono text-[var(--success)] font-bold flex items-center gap-1 uppercase">
              <span className="w-1.5 h-1.5 bg-[var(--success)] rounded-full animate-pulse" aria-hidden="true" /> Live
            </span>
          </div>
          
          <div className="flex-1 overflow-y-auto divide-y divide-[var(--border-subtle)] max-h-64 lg:max-h-none" role="log" aria-label="Live diagnostic stream">
            {recentRecords.length > 0 ? recentRecords.map((r) => {
              const isHigh = r.prediction.toLowerCase().includes("high") || r.prediction.toLowerCase().includes("positive");
              return (
                <div key={r.id} className="p-3 hover:bg-[rgba(255,255,255,0.01)] transition-colors group cursor-pointer">
                  <div className="flex justify-between items-start mb-1.5">
                    <div className="flex items-center gap-1.5">
                      <span className={`w-1.5 h-1.5 rounded-full ${isHigh ? "bg-[var(--danger)]" : "bg-[var(--success)]"}`} aria-hidden="true" />
                      <span className="text-xs font-bold text-[var(--text-primary)] uppercase tracking-wide">{r.record_type}</span>
                    </div>
                    <span className="mono-meta text-[10px]">{new Date(r.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                  </div>
                  <div className="flex justify-between items-center text-[10px] font-mono text-[var(--text-secondary)]">
                    <span>ID: #{r.id}</span>
                    <span className={`px-2 py-0.5 rounded-sm border ${
                      isHigh 
                        ? "bg-[var(--danger-muted)] text-[var(--danger)] border-[var(--danger-border)]" 
                        : "bg-[var(--success-muted)] text-[var(--success)] border-[var(--success-border)]"
                    }`}>
                      {r.prediction.substring(0, 18)}...
                    </span>
                  </div>
                </div>
              );
            }) : (
              <div className="p-8 text-center text-xs text-[var(--text-dim)] font-mono uppercase tracking-wide">
                {loading ? "Syncing Diagnostic Streams..." : "No stream logs recorded"}
              </div>
            )}
          </div>
          
          <div className="p-2 border-t border-[var(--border)] bg-[rgba(15,15,17,0.5)]">
            <Link to="/patients" onMouseEnter={() => prefetchRoute('/patients')} className="w-full block text-center text-[10px] text-[var(--text-secondary)] hover:text-[var(--accent)] font-bold tracking-wider uppercase transition-colors">
              View Log History
            </Link>
          </div>
        </div>
      </div>

      <OperationsCockpit />

      {/* Level 3: Department Load & Resources */}
      <div className="panel overflow-hidden">
        <div className="panel-header bg-[rgba(15,15,17,0.5)]">
          <h2 className="section-title">Department Load Allocations</h2>
        </div>
        <div className="p-4 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6" role="region" aria-label="Department load indicators">
          {(telemetry ? telemetry.department_loads : [
            { dept: "Cardiology", load: 88, status: "Critical" },
            { dept: "Pulmonology", load: 64, status: "Stable" },
            { dept: "Nephrology", load: 42, status: "Optimal" },
            { dept: "Endocrinology", load: 76, status: "Elevated" },
          ]).map((dept) => (
            <div key={dept.dept} className="space-y-2">
              <div className="flex justify-between text-[11px] font-mono uppercase tracking-wider">
                <span className="text-[var(--text-secondary)]">{dept.dept}</span>
                <span className={dept.load > 80 ? "text-[var(--danger)] font-bold" : dept.load > 70 ? "text-[var(--warning)] font-bold" : "text-[var(--success)] font-bold"}>{dept.load}%</span>
              </div>
              <div className="h-1.5 w-full bg-[var(--border)] rounded-full overflow-hidden">
                <motion.div
                  initial={{ width: 0 }}
                  animate={{ width: `${dept.load}%` }}
                  transition={{ duration: 0.8, ease: "easeOut" }}
                  className={`h-full ${dept.load > 80 ? "bg-[var(--danger)]" : dept.load > 70 ? "bg-[var(--warning)]" : "bg-[var(--success)]"}`}
                  role="progressbar"
                  aria-valuenow={dept.load}
                  aria-valuemin={0}
                  aria-valuemax={100}
                  aria-label={`${dept.dept} load: ${dept.load}%`}
                />
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
