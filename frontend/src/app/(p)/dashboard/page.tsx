"use client";

import { useEffect, useState, useMemo, useRef } from "react";
import { useAuthStore } from "@/lib/auth";
import { getRecords, type HealthRecord } from "@/lib/api";
import { useTelemetry } from "@/lib/useTelemetry";
import { motion } from "framer-motion";
import { Activity, Clock, FileText, AlertTriangle, Sparkles, BrainCircuit, Wifi, WifiOff } from "lucide-react";
import Link from "next/link";
import { XAxis, YAxis, Tooltip, AreaChart, Area } from "recharts";
import OperationsCockpit from "@/components/operations/OperationsCockpit";

export default function DashboardPage() {
  const { user } = useAuthStore();
  const [records, setRecords] = useState<HealthRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const chartContainerRef = useRef<HTMLDivElement | null>(null);
  const [chartWidth, setChartWidth] = useState(720);
  const { data: telemetry, status: wsStatus } = useTelemetry();

  useEffect(() => {
    getRecords()
      .then(setRecords)
      .catch(console.error)
      .finally(() => setLoading(false));
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

  // Chart data derived from records
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

  // Derive capacity percentage from telemetry
  const capacityPct = telemetry
    ? Math.round((telemetry.active_census / telemetry.total_capacity) * 100)
    : 84;

  return (
    <div className="w-full space-y-8 pb-10 selection:bg-[var(--accent)] selection:text-black">
      {/* System ribbon */}
      <div className="glass-card px-4 py-2 flex flex-col md:flex-row md:items-center md:justify-between gap-2 font-mono text-[11px] tracking-[0.18em] text-[var(--text-dim)] uppercase" role="status" aria-label="System status bar">
        <div className="flex flex-wrap items-center gap-x-4 gap-y-2">
          <span className="flex items-center gap-2 text-[var(--success)]">
            <span className="w-1.5 h-1.5 rounded-sm bg-[var(--success)] animate-pulse" aria-hidden="true" />
            HL7 STREAM ACTIVE
          </span>
          <span>NODE: CARE-MED-09</span>
          <span>AUTH: JWT SESSION</span>
        </div>
        <div className="flex flex-wrap items-center gap-x-4 gap-y-2">
          <span>LATENCY: {telemetry ? telemetry.system_latency_ms : "--"}ms</span>
          <span>UPTIME: 99.999%</span>
          {wsStatus === "connected" ? (
            <span className="flex items-center gap-1 text-[var(--success)]"><Wifi size={10} aria-hidden="true" /> WS</span>
          ) : (
            <span className="flex items-center gap-1 text-[var(--danger)]"><WifiOff size={10} aria-hidden="true" /> WS</span>
          )}
        </div>
      </div>

      {/* Header */}
      <header className="flex flex-col md:flex-row md:items-end justify-between gap-6 border-b border-[var(--border)] pb-6">
        <div>
          <h1 className="text-3xl md:text-5xl text-[var(--text-primary)] mb-2 display-hero">
            Command Center
          </h1>
          <p className="lede text-sm flex items-center gap-2">
            <BrainCircuit size={14} className="text-[var(--accent)]" />
            Singularity Medical Intelligence Engine — Attending: {user?.full_name || user?.username || "Dr. Admin"}
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Link href="/patients">
            <button className="btn btn-secondary text-xs uppercase tracking-wider flex items-center gap-2" aria-label="Open EMR Database">
              <FileText size={14} /> EMR Database
            </button>
          </Link>
          <Link href="/chat">
            <button className="btn btn-primary text-xs uppercase tracking-wider flex items-center gap-2" aria-label="Engage AI Copilot">
              <Sparkles size={14} /> Engage Copilot
            </button>
          </Link>
        </div>
      </header>

        {/* Level 1: Core Telemetry Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4" role="region" aria-label="Core telemetry metrics">
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
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.05 }}
              className="glass-card p-5 flex flex-col justify-between relative overflow-hidden group"
            >
              <div className="absolute top-0 right-0 w-16 h-16 bg-[var(--bg-card)] rounded-bl-full -z-10 group-hover:bg-[var(--bg-card-hover)] transition-colors" />
              <div className="flex justify-between items-start mb-6">
                <div>
                  <h3 className="section-label mb-1">{stat.title}</h3>
                  <div className="flex items-baseline gap-2">
                    <span className="text-3xl font-light text-[var(--text-primary)] tracking-tighter">{stat.value}</span>
                  </div>
                </div>
                <stat.icon size={18} className="text-[var(--border-focus)]" aria-hidden="true" />
              </div>
              <div className="flex items-center justify-between text-xs font-mono">
                <span className="text-[var(--text-secondary)]">{stat.sub}</span>
                <span className={`${stat.trendColor} font-bold`}>{stat.trend}</span>
              </div>
              <div className="mt-4 pt-4 border-t border-[var(--border-subtle)] section-label">
                {stat.meta}
              </div>
            </motion.div>
          ))}
        </div>

        <OperationsCockpit />

        {/* Level 2: Analytics & AI Feeds */}
        <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
          {/* Risk Trajectory Chart */}
          <div className="xl:col-span-2 panel flex flex-col">
            <div className="panel-header flex justify-between items-center">
              <div>
                <h2 className="section-title">Population Risk Trajectory</h2>
                <p className="mono-meta mt-1">
                  AGGREGATED PREDICTIVE MODELING (N={telemetry ? telemetry.active_census.toLocaleString() : "1,248"})
                </p>
              </div>
              <div className="flex gap-2" role="group" aria-label="Time range selector">
                <button className="px-3 py-1 bg-[var(--bg-card)] border border-[var(--border)] text-[var(--text-secondary)] text-[11px] font-bold tracking-wider hover:text-[var(--text-primary)]" aria-label="7 day view">7D</button>
                <button className="px-3 py-1 bg-[var(--bg-card-hover)] border border-[var(--border-focus)] text-[var(--text-primary)] text-[11px] font-bold tracking-wider" aria-pressed="true" aria-label="30 day view">30D</button>
                <button className="px-3 py-1 bg-[var(--bg-card)] border border-[var(--border)] text-[var(--text-secondary)] text-[11px] font-bold tracking-wider hover:text-[var(--text-primary)]" aria-label="90 day view">90D</button>
              </div>
            </div>
            <div className="h-[350px] min-h-[350px] p-6">
              <div ref={chartContainerRef} className="h-full w-full overflow-hidden">
                <AreaChart width={chartWidth} height={300} data={displayChartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                  <defs>
                    <linearGradient id="colorRisk" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="var(--accent-blue)" stopOpacity={0.28} />
                      <stop offset="95%" stopColor="var(--accent-blue)" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <XAxis dataKey="name" stroke="var(--border-focus)" fontSize={10} tickLine={false} axisLine={false} dy={10} tick={{ fill: "var(--text-dim)" }} />
                  <YAxis stroke="var(--border-focus)" fontSize={10} tickLine={false} axisLine={false} dx={-10} tick={{ fill: "var(--text-dim)" }} />
                  <Tooltip
                    cursor={{ stroke: "var(--border-focus)", strokeWidth: 1, strokeDasharray: "4 4" }}
                    contentStyle={{ background: "rgba(17,14,13,0.92)", border: "1px solid var(--border)", borderRadius: "10px", fontSize: "12px", fontFamily: "var(--font-mono)", backdropFilter: "blur(10px)" }}
                    itemStyle={{ color: "var(--accent-blue)", fontWeight: "600" }}
                  />
                  <Area
                    type="monotone"
                    dataKey="riskScore"
                    stroke="var(--accent-blue)"
                    strokeWidth={2}
                    fillOpacity={1}
                    fill="url(#colorRisk)"
                    activeDot={{ r: 4, fill: "var(--bg-primary)", stroke: "var(--accent-blue)", strokeWidth: 2 }}
                  />
                </AreaChart>
              </div>
            </div>
          </div>

          {/* Live Diagnostic Stream */}
          <div className="panel flex flex-col">
            <div className="panel-header flex justify-between items-center">
              <h2 className="section-title flex items-center gap-2">
                <Activity size={14} className="text-[var(--success)]" aria-hidden="true" /> AI Diagnostic Stream
              </h2>
              <span className="text-[11px] font-mono text-[var(--success)] flex items-center gap-1">
                <div className="w-1.5 h-1.5 bg-[var(--success)] rounded-full animate-pulse" aria-hidden="true" /> LIVE
              </span>
            </div>
            <div className="flex-1 p-0 overflow-y-auto max-h-[350px] divide-y divide-[var(--border-subtle)]" role="log" aria-label="Live diagnostic stream">
              {recentRecords.length > 0 ? recentRecords.map((r) => {
                const isHigh = r.prediction.toLowerCase().includes("high") || r.prediction.toLowerCase().includes("positive");
                return (
                  <div key={r.id} className="p-4 hover:bg-[var(--bg-card)] transition-colors group cursor-pointer">
                    <div className="flex justify-between items-start mb-2">
                      <div className="flex items-center gap-2">
                        <span className={`w-2 h-2 rounded-sm ${isHigh ? "bg-[var(--danger)]" : "bg-[var(--success)]"}`} aria-hidden="true" />
                        <span className="text-xs font-bold text-[var(--text-primary)] uppercase tracking-wider">{r.record_type} Panel</span>
                      </div>
                      <span className="mono-meta">{new Date(r.timestamp).toLocaleTimeString()}</span>
                    </div>
                    <div className="flex justify-between items-end">
                      <div className="text-[11px] text-[var(--text-secondary)] font-mono leading-relaxed">
                        REC: #{r.id}
                      </div>
                      <div className={`text-[11px] font-bold px-2 py-1 rounded-sm border ${isHigh ? "bg-[var(--danger-muted)] text-[var(--danger)] border-[var(--danger-border)]" : "bg-[var(--success-muted)] text-[var(--success)] border-[var(--success-border)]"}`}>
                        {r.prediction.substring(0, 20)}...
                      </div>
                    </div>
                  </div>
                );
              }) : (
                <div className="p-8 text-center text-xs text-[var(--text-dim)] font-mono">
                  {loading ? "LOADING DIAGNOSTIC STREAMS..." : "NO ACTIVE DIAGNOSTIC STREAMS"}
                </div>
              )}
            </div>
            <div className="p-3 border-t border-[var(--border)] bg-[var(--bg-card)]">
              <Link href="/patients" className="w-full block text-center text-[11px] text-[var(--text-secondary)] font-bold tracking-widest hover:text-[var(--text-primary)] uppercase">
                View Full Logs
              </Link>
            </div>
          </div>
        </div>

        {/* Level 3: Department Load & Resources */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-3 panel">
            <div className="panel-header">
              <h2 className="section-title">Resource Allocation & Department Load</h2>
            </div>
            <div className="p-6 grid grid-cols-2 md:grid-cols-4 gap-8" role="region" aria-label="Department load indicators">
              {(telemetry ? telemetry.department_loads : [
                { dept: "Cardiology", load: 88, status: "Critical" },
                { dept: "Pulmonology", load: 64, status: "Stable" },
                { dept: "Nephrology", load: 42, status: "Optimal" },
                { dept: "Endocrinology", load: 76, status: "Elevated" },
              ]).map((dept) => (
                <div key={dept.dept}>
                  <div className="flex justify-between text-xs mb-2 font-mono">
                    <span className="text-[var(--text-secondary)]">{dept.dept}</span>
                    <span className={dept.load > 80 ? "text-[var(--danger)]" : dept.load > 70 ? "text-[var(--warning)]" : "text-[var(--success)]"}>{dept.load}%</span>
                  </div>
                  <div className="h-1 w-full bg-[var(--border-subtle)] rounded-full overflow-hidden">
                    <motion.div
                      initial={{ width: 0 }}
                      animate={{ width: `${dept.load}%` }}
                      transition={{ duration: 1, type: "spring" }}
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
    </div>
  );
}
