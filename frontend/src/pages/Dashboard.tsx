import { useEffect, useState, useMemo, useRef } from "react";
import { useAuthStore } from "@/lib/auth";
import { getRecords, getDemoReadiness, type HealthRecord } from "@/lib/api";
import { useTelemetry } from "@/lib/useTelemetry";
import { motion } from "framer-motion";
import { Activity, Clock, FileText, AlertTriangle, Sparkles, BrainCircuit, Wifi, WifiOff } from "lucide-react";
import { Link } from "react-router-dom";
import { XAxis, YAxis, Tooltip, AreaChart, Area, ResponsiveContainer } from "recharts";
import OperationsCockpit from "@/components/operations/OperationsCockpit";
import { prefetchRoute } from "@/lib/prefetch";
import { useTranslation } from "@/lib/i18n";

export default function DashboardPage() {
  const { user } = useAuthStore();
  const { t } = useTranslation();
  const [records, setRecords] = useState<HealthRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const chartContainerRef = useRef<HTMLDivElement | null>(null);
  const [chartWidth, setChartWidth] = useState(720);
  const { data: telemetry, status: wsStatus } = useTelemetry();
  const [demoReadiness, setDemoReadiness] = useState<{ status: string } | null>(null);
  const [error, setError] = useState("");

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

  useEffect(() => {
    const element = chartContainerRef.current;
    if (!element || typeof ResizeObserver === "undefined") return;

    const observer = new ResizeObserver(([entry]) => {
      setChartWidth(Math.max(320, Math.floor(entry.contentRect.width)));
    });
    observer.observe(element);
    return () => observer.disconnect();
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

  return (
    <div className="w-full space-y-6 pb-12 selection:bg-[var(--accent)] selection:text-white">
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
          <h1 className="text-xl font-bold text-[var(--text-primary)] uppercase tracking-wider">
            {t.commandCenter}
          </h1>
          <p className="text-xs text-[var(--text-secondary)] font-mono uppercase tracking-wide flex items-center gap-1.5 mt-1">
            <BrainCircuit size={12} className="text-[var(--accent)]" />
            {t.welcome}: {user?.full_name || user?.username || "Dr. Admin"}
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

      {/* Level 1: Core Telemetry Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4" role="region" aria-label="Core telemetry metrics">
        {[
          {
            title: "ACTIVE CENSUS",
            value: telemetry ? telemetry.active_census.toLocaleString() : "--",
            sub: `${capacityPct}% Capacity`,
            icon: Activity,
            trend: telemetry ? `${telemetry.active_census}/${telemetry.total_capacity}` : "+12",
            trendColor: capacityPct > 85 ? "text-[var(--danger)]" : "text-[var(--warning)]",
            meta: telemetry ? `ED Boarding: ${telemetry.ed_boarding}` : "ICU: 42/50",
          },
          {
            title: "AI TRIAGE ALERTS",
            value: highRiskRecords.length.toString(),
            sub: "Requires Review",
            icon: AlertTriangle,
            trend: highRiskRecords.length > 0 ? "CRITICAL" : "CLEAR",
            trendColor: highRiskRecords.length > 0 ? "text-[var(--danger)]" : "text-[var(--success)]",
            meta: "Sepsis Risk: 2",
          },
          {
            title: "PREDICTIVE MODELS",
            value: "98.4%",
            sub: "Global Accuracy",
            icon: BrainCircuit,
            trend: "STABLE",
            trendColor: "text-[var(--success)]",
            meta: `Running: ${telemetry ? telemetry.ai_nodes_active : 14} Nodes`,
          },
          {
            title: "SYSTEM LATENCY",
            value: telemetry ? `${telemetry.system_latency_ms}ms` : "--",
            sub: "Protected Session",
            icon: Clock,
            trend: "OPTIMAL",
            trendColor: "text-[var(--success)]",
            meta: "FHIR Bridge: UP",
          },
        ].map((stat, i) => (
          <motion.div
            key={i}
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.04 }}
            className="glass-card p-4 flex flex-col justify-between relative overflow-hidden group border border-[var(--border)] rounded bg-[rgba(24,24,27,0.4)]"
          >
            <div className="flex justify-between items-start mb-4">
              <div>
                <h3 className="section-label mb-1">{stat.title}</h3>
                <div className="flex items-baseline gap-1">
                  <span className="text-2xl font-bold text-[var(--text-primary)] tracking-tight">{stat.value}</span>
                </div>
              </div>
              <div className="p-1.5 rounded bg-[rgba(255,255,255,0.02)] border border-[var(--border)] text-[var(--text-dim)] group-hover:text-[var(--accent)] transition-colors">
                <stat.icon size={14} aria-hidden="true" />
              </div>
            </div>
            
            <div className="flex items-center justify-between text-[11px] font-mono border-t border-[var(--border-subtle)] pt-2.5 mt-2">
              <span className="text-[var(--text-secondary)]">{stat.sub}</span>
              <span className={`${stat.trendColor} font-bold`}>{stat.trend}</span>
            </div>
            
            <div className="text-[10px] font-mono text-[var(--text-muted)] mt-1.5 flex justify-between uppercase">
              <span>Status</span>
              <span>{stat.meta}</span>
            </div>
          </motion.div>
        ))}
      </div>

      <OperationsCockpit />

      {/* Level 2: Analytics & AI Feeds */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        
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
            <div ref={chartContainerRef} className="h-64 w-full overflow-hidden flex items-center justify-center">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={displayChartData} margin={{ top: 10, right: 5, left: -25, bottom: 0 }}>
                  <defs>
                    <linearGradient id="colorRisk" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="var(--accent)" stopOpacity={0.25} />
                      <stop offset="95%" stopColor="var(--accent)" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <XAxis dataKey="name" stroke="var(--border-focus)" fontSize={9} tickLine={false} axisLine={false} dy={5} tick={{ fill: "var(--text-dim)" }} />
                  <YAxis stroke="var(--border-focus)" fontSize={9} tickLine={false} axisLine={false} dx={-5} tick={{ fill: "var(--text-dim)" }} />
                  <Tooltip
                    cursor={{ stroke: "var(--border-focus)", strokeWidth: 1 }}
                    contentStyle={{ background: "rgba(24,24,27,0.95)", border: "1px solid var(--border-focus)", borderRadius: "6px", fontSize: "11px", fontFamily: "var(--font-mono)", backdropFilter: "blur(12px)" }}
                    itemStyle={{ color: "var(--accent)", fontWeight: "700" }}
                  />
                  <Area
                    type="monotone"
                    dataKey="riskScore"
                    stroke="var(--accent)"
                    strokeWidth={1.5}
                    fillOpacity={1}
                    fill="url(#colorRisk)"
                    activeDot={{ r: 4, fill: "var(--bg-primary)", stroke: "var(--accent)", strokeWidth: 1.5 }}
                  />
                </AreaChart>
              </ResponsiveContainer>
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
